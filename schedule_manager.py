#!/usr/bin/python
# from job import Job
import json
from ardio import Led
from time import sleep
import os
from models import *  # Zone, Route, Group, IntermediaryZoneGroup
from playhouse.shortcuts import model_to_dict
from box import Box
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging.config
from datetime import *
import logging_tree
"""
logging.basicConfig(
    filename="schedulerManager.log",
    format='[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s: %(message)s',
    level=logging.INFO)
from datetime import datetime, timedelta
"""
# logger = logging.getLogger('apscheduler')


def job_to_dict(job):
    return {
            'id': job.id,
            'func': job.func_ref,
            'trigger': str(job.trigger),
            'executor': job.executor,
            'args': job.args,
            'kwargs': job.kwargs,
            'name': job.name,
            'misfire_grace_time': job.misfire_grace_time,
            'coalesce': job.coalesce,
            'max_instances': job.max_instances,
            'next_run_time': job.next_run_time
        }


class ScheduleManager(object):
    """This class manages the creation and execution of schedules.
    It provides APIs necessary to create, update and delete schedules.
    Startup steps:
        load config file
        load IO zones
        load jobs from config
    """

    def __init__(self):
        """Loads schedules,
            initiliazes zones
        """
        self.configs = self.load_configs("config.json")
        # logging_tree.printout()

        logger = logging.getLogger(__name__)
        logger.info("SchedIt Starting up")
        self.jobs = []
        self.scheduler = BackgroundScheduler()
        db = self.configs['db']
        self.scheduler.add_jobstore(
            'sqlalchemy',
            url='mysql://{}:{}@{}/{}'.format(
                db['username'],
                db['password'],
                db['host'],
                db['name'])
        )
        # loads zones from DB
        self.load_zones()
    #    self.load_schedules()

        print "scheduler Started"
        logger.info("Started")
        self.start()

    def load_configs(self, config):
        """Loads pre-configured schedules from file
        Returns dictionary with schedules.
        """
        # logger.info("Loading configs from '{}'".format(config))
        with open(config) as file:
            data = file.read()
            data = json.loads(data)
            logging.config.dictConfig(data["logging"])
        return data

    def load_zones(self):
        """Loads I/O zones from config file"""
        logger = logging.getLogger(__name__)

        logger.info("Loading zones")
        zones = Zone.select()
        out = []
        for zone in zones:
            out.append(model_to_dict(zone))
            z = Led(zone.pin, zone.name)
            z.on()
            sleep(1)
            z.off()
        logger.info(
            "Loading complete. {} zones initialized.".format(len(zones)))

    def add_schedule(self, schedule):
        """Adds job schedule to job store and schedules job for execution.
        """
        schedule = Box(schedule)
        logger = logging.getLogger(__name__)
        logger.info("add_schedule called")
        logger.info("Scheduling  {}".format(schedule))
        # print schedule.start_time
        # hour, minute, second = schedule.start_time.split(":")
        # logger.info("{} {} {}".format(hour, minute, second))

        t = datetime.now()
        dt = datetime.now() + timedelta(seconds=5)
        # print str(t), str(dt)
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        # print str(hour), str(minute), str(second)
        # minute = schedule.start_time.split[":"][1]
        # second = schedule.start_time.split[':'][2]  # or "00"
        logger.info("schedule will run at {}:{}:{}".format(
            str(hour), str(minute), str(second)))

        days = schedule.days

        job = self.scheduler.add_job(
            execute,
            'cron',
            day_of_week=days,
            hour=hour,
            minute=minute,
            second=second,
            kwargs=schedule)
        logger.warning("schedule scheduled")

        return job_to_dict(job)

    def get_job(self, id):
        for s in self.scheduler.get_jobs():
            if int(s.id) == id:
                logger.info("i found it")
                return s
        logger.info("Job {} not found".format(id))
        return None

    def get_schedules(self, active_only=False):
        """Returns JSON dict of schedules`"""
        logger.info("getting schedules")
        active_schedules = []
        schedules = self.scheduler.get_jobs()
        for schedule in schedules:
            if ((schedule.kwargs['is_enabled'] == active_only) or not active_only):
                _schedule = schedule.kwargs
                _schedule['id'] = schedule.id
               # active_jobs.append(job.to_json())
                active_schedules.append(_schedule)
        logger.info("active schedules: {}".format(active_schedules))
        return active_schedules

    def start(self):
        print(
            'Press Ctrl+{0} to exit'
            .format('Break' if os.name == 'nt' else 'C'))
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.scheduler.shutdown()


def execute(**schedule):
    print "hello execute outside"
    """
        turn on source zone
        turn on passthrough zones
        for zone n target zones:
            turn on zone
            pass time
            turn off zone
    """
    print "execute executing"
    schedule = Box(schedule)
    route = Box(get_route(schedule.route))
    sz = route.source_zone
    tz = route.target_group.zones
    pz = route.passthrough_group.zones

    source = Led(name=sz.name, pin=sz.pin)
    target_zones = [Led(name=zone.name, pin=zone.pin) for zone in tz]
    passthrough_zones = [Led(name=zone.name, pin=zone.pin) for zone in pz]

    logger.info("Turning on source zone [zoneId: {}".format(source.getName))
    source.on()

    for idx, zone in enumerate(passthrough_zones):
        logger.info(
            "Turning on passthrough zone - {} - [{} of {}]".format(zone.getName(), idx + 1, len(passthrough_zones)))
        zone.on()
        sleep(schedule.zone_delay)

    for idx, zone in enumerate(target_zones):
        logger.info(
            "Turning on target zone - {} - [{} of {}]".format(zone.getName(), idx + 1, len(target_zones)))

        zone.on()
        sleep(schedule.duration)
        logger.info(
            "Turning off target zone - {} - [{} of {}]".format(zone.getName(), idx + 1, len(target_zones)))
        zone.off()
        sleep(schedule.zone_delay)

    for idx, zone in enumerate(passthrough_zones):
        logger.info("Turning off passthrough zone - {} - [{} of {}]".format(
            zone.getName(), idx + 1, len(passthrough_zones)))
        zone.off()
        sleep(schedule.zone_delay)

    logger.info("Turning off source zone - {} -".format(source.getName()))
    source.off()

    logger.info("Executing schedule {}".format(schedule.id))
