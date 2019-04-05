#!/usr/bin/python
# from job import Job
import json
from ardio import Led
from time import sleep
import os
from models import *  # Zone, Route, Group, IntermediaryZoneGroup
from playhouse.shortcuts import model_to_dict
from box import Box
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging.config
from datetime import *

"""
logging.basicConfig(
    filename="schedulerManager.log",
    format='[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s: %(message)s',
    level=logging.INFO)
from datetime import datetime, timedelta
"""
logger = logging.getLogger('apscheduler')


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
        logger = logging.getLogger(__name__)
        logger.info("SchedIt Starting up")
        self.jobs = []
        self.scheduler = BlockingScheduler()
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
        self.load_schedules()

        self.start()

    def load_configs(self, config):
        """Loads pre-configured schedules from file
        Returns dictionary with schedules.
        """
        logger.info("Loading configs from '{}'".format(config))
        with open(config) as file:
            data = file.read()
            data = json.loads(data)
            logging.config.dictConfig(data["logging"])
        return data

    def load_schedules(self):
        """Loads schedules on startup
        """
        logger = logging.getLogger(__name__)
        logger.info("Loading schedules")
        schedules = Schedule.select()
        for schedule in schedules:
            print schedule

            # datetime.time object is not serializable
            # convert datetime.time object outside of model_to_dict
            schedule.start_time = str(schedule.start_time)
            schedule = model_to_dict(schedule)

            route = Route.get(schedule["route"]["id"])
            route = model_to_dict(route)

            schedule["route"]["passthrough_group"]["zones"] = get_group_zones(
                route["passthrough_group"]["id"])
            # print json.dumps(schedule, sort_keys=True, indent=4)
            schedule["route"]["target_group"]["zones"] = get_group_zones(
                route["target_group"]["id"])

            print "after:", json.dumps(schedule, sort_keys=True, indent=4)
            logger.debug("Loading schedule config: '{}'".format(
                json.dumps(schedule)))

            schedule = Box(schedule)

            self.add_schedule(schedule)
        logger.info("Loading complete. {} jobs loaded.".format(len(schedules)))

    def load_schedule(self, schedule):
        self.add_schedule(schedule)

    def load_zones(self):
        """Loads I/O zones from config file"""
        logger = logging.getLogger(__name__)

        logger.info("Loading zones")
        zones = Zone.select()
        out = []
        for zone in zones:
            out.append(model_to_dict(zone))
            z = Led(zone.pin, zone.name)
            z.off()
        logger.info("Loading complete. {} zones loaded.".format(len(zones)))

    def add_schedule(self, schedule):
        """Adds job schedule to job store and schedules job for execution.
        """
        logger = logging.getLogger(__name__)
        logger.info("Scheduling schedule {}".format(schedule.id))

        hour, minute, second = schedule.start_time.split(":")
        print hour, minute, second
        t = datetime.now()
        dt = datetime.now() + timedelta(seconds=3)

        print str(t), str(dt)
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        print str(hour), str(minute), str(second)
        # minute = schedule.start_time.split[":"][1]
        # second = schedule.start_time.split[':'][2]  # or "00"
        days = schedule.days
        self.scheduler.add_job(
            execute,
            'cron',
            day_of_week=days,
            hour=hour,
            minute=minute,
            second=second,
            kwargs=schedule)
        logger.warning("schedule scheduled")

    def remove_job(self, id):
        """Removes job dictionary from list of schedules.
        """
        logger.info("Removing job {}".format(id))
        for job in self.jobs:
            logger.debug(str(job))
            if job.id == id:
                self.jobs.remove(job)
                logger.info("Job {} successfully removed.".format(id))
                return
        logger.info("Job {} not found".format(id))
        return

    def get_zone(self, id):
        for z in self.zones:
            if z["id"] == id:
                logger.debug("Zone {} found it".format(id))
                return z
        logger.error("Zone {} not found in config file!".format(id))
        return None

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
            pass

    def execute(**k):
        print "hello execute"


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
    schedule = Box(schedule)
    sz = schedule.route.source_zone
    tz = schedule.route.target_group.zones
    pz = schedule.route.passthrough_group.zones

    source = Led(name=sz.name, pin=sz.pin)
    target_zones = [Led(name=zone.name, pin=zone.pin) for zone in tz]
    passthrough_zones = [Led(name=zone.name, pin=zone.pin) for zone in pz]

    logger.info("Turning on source zone [zoneId: {}".format(source.getName))
    source.on()

    for idx, zone in enumerate(passthrough_zones):
        logger.info(
            "Turning on passthrough zone - {} - [{} of {}]".format(zone.getName(), idx + 1, len(passthrough_zones)))
        zone.on()
        sleep(0.5)

    for idx, zone in enumerate(target_zones):
        logger.info(
            "Turning on target zone - {} - [{} of {}]".format(zone.getName(), idx + 1, len(target_zones)))

        zone.on()
        sleep(schedule.duration)
        logger.info(
            "Turning off target zone - {} - [{} of {}]".format(zone.getName(), idx + 1, len(target_zones)))
        zone.off()
        sleep(0.5)

    for idx, zone in enumerate(passthrough_zones):
        logger.info("Turning off passthrough zone - {} - [{} of {}]".format(
            zone.getName(), idx + 1, len(passthrough_zones)))
        zone.off()
        sleep(0.5)

    logger.info("Turning off source zone - {} -".format(source.getName()))
    source.off()

    logger.info("Executing schedule {}".format(schedule.id))


"""
    for zone in schedule.route:
        _zone = sched.get_zone(zone)
        zone_led = Led(_zone["pin"], _zone["name"])
        logger.info("Turning on zone")
        zone_led.on()
        sleep(zone_delay)

        if power_led:
            logger.info("Turning on power-zone")
            power_led.on()
            sleep(zone_delay)

        sleep(duration)

        if power_led:
            power_led.off()
            sleep(zone_delay)

        zone_led.off()
        sleep(zone_delay)

    if pre_led:
        pre_led.off()

    logger.info("Yay! Job complete")


"""


sm = ScheduleManager()
"""sm.remove_job(4)
sm.add_job({
        "id": 4,
        "name": "four",
        "days": "*",
        "start_time": "21:59",
        "duration": 5,
        "zones": [2, 3],
        "pre_zone": 7,
        "power_zone": 6,
        "zone_delay": 2,
        "is_active": True
})
l = []"""
# print json.dumps(sm.get_schedules())
"""sm.remove_job(4)
for j in sm.get_jobs():
    l.append(j)
"""
# print sm.scheduler.get_jobs()[0].kwargs

# sched = ScheduleManager()
# def execute(id, name, is_active, start_time, days, duration, zones, pre_zone, power_zone, zone_delay):
"""def execute(**kwargs):
    logger = logging.getLogger(__name__)
    logger.info(
        "Running execute for scheduled job ID #{} ({}) ".format(id, name))

    if pre_zone:
        _pre_zone = sched.get_zone(pre_zone)
        pre_led = Led(_pre_zone["pin"], _pre_zone["name"])
        logger.warning("Pre-zone found.")
    else:
        logger.warning("No pre-zone found.")
        pre_led = None

    if power_zone:
        _power_zone = sched.get_zone(power_zone)
        power_led = Led(_power_zone["pin"], _power_zone["name"])
        logger.warning("Power-zone found.")
    else:
        logger.warning("No power-zone found.")
        power_led = None

    # if main, turn on
    if pre_led:
        logger.info("Turning on pre-zone")
        pre_led.on()
        sleep(zone_delay)

    # turn on source
    # turn on passthrough group
    # cycle through target group

    route = Route.get(id)
    out = model_to_dict(route)
    print out
    out['passthrough_group']['zones'] = get_group_zones(
        route.passthrough_group.id)
    out['target_group']['zones'] = get_group_zones(
        route.target_group.id)

    logger.info("{} zones found".format(zones))
    for zone in zones:
        _zone = sched.get_zone(zone)
        zone_led = Led(_zone["pin"], _zone["name"])
        logger.info("Turning on zone")
        zone_led.on()
        sleep(zone_delay)

        if power_led:
            logger.info("Turning on power-zone")
            power_led.on()
            sleep(zone_delay)

        logger.info("All zones turned. Worker fully started.")
        sleep(duration)
        logger.info("Worker completed. Shutting down execute.")

        if power_led:
            power_led.off()
            sleep(zone_delay)

        zone_led.off()
        sleep(zone_delay)

    if pre_led:
        pre_led.off()

    logger.info("Yay! Job complete")


"""
