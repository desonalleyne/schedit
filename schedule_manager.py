#!/usr/bin/python
from job import Job 
import json
from ardio import Led
from time import sleep
from datetime import datetime, timedelta
import os
from apscheduler.schedulers.blocking import BlockingScheduler
#from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging
logging.basicConfig(filename="schedulerManager.log", format='[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s: %(message)s', level=logging.DEBUG)


logger = logging.getLogger(__name__)

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
        logger.info("SchedIt Starting up")
        self.configs = self.load_configs("config.json")
        self.jobs = []
        self.scheduler = BlockingScheduler()
        db = selc.configs.db
	self.scheduler.add_jobstore('sqlalchemy', url='mysql://{}:{}@{}/{}'.format(db.username, db.password, db.host, db.name))
        self.load_zones(self.configs)
        #self.load_jobs(self.configs)
#	self.start()

    def load_configs(self, config):
        """Loads pre-configured schedules from file
        Returns dictionary with schedules.
        """
        logger.info("Loading configs from '{}'".format(config))
        with open(config) as file:
            data = file.read()
            data = json.loads(data)
        return data

    def load_jobs(self,configs):
        """Loads jobs on startup
        """
        logger.info("Loading jobs")
        # create jobs from config file
        for job in configs["jobs"]:
            print "loading a ", type(job)
            self.add_job(job)
        logger.info("Loading complete. {} jobs loaded.".format(len(self.jobs)))

    def load_zones(self,data):
        """Loads I/O zones from config file"""

        logger.info("Loading zones")
        self.zones = data["zones"]
        for zone in self.zones:
            z = Led(zone["pin"])
            z.off()
        logger.info("Loading complete. {} zones loaded.".format(len(self.jobs)))

    def add_job(self,job):
        """Adds job schedule to job store and schedules job for execution.
        """
	logger.info("Scheduling job {}".format(job['id']))
	hour = job['start_time'][:2]
	minute = job['start_time'][3:5]
	second = job['start_time'][6:8] or "00"
	days = job['days']
	self.scheduler.add_job(execute, 'cron',  day_of_week=days, hour=hour, minute=minute, second=second, kwargs=job)
	logger.warning("job scheduled")

    def remove_job(self,id):
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

    def get_jobs(self,active_only = False):
        """Returns JSON dict of jobs""" 
        logger.info("getting jobs")
        active_jobs = [] 
        jobs = self.scheduler.get_jobs()
        for job in jobs:
        #for job in self.jobs:
            if ((job.kwargs['is_active'] == active_only) or not active_only):
                _job = job.kwargs
                _job['id'] = job.id
               # active_jobs.append(job.to_json())
                active_jobs.append(_job)
        logger.info("active jobs: {}".format(active_jobs))
        return active_jobs


    def start(self):
       print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            pass
"""sm = ScheduleManager()
sm.remove_job(4)
sm.add_job({
        "id": 4,
        "name": "four",
        "days": "*",
        "start_time": "22:02",
        "duration": 5,
        "zones": [2,3],
        "pre_zone": 1, 
        "power_zone":4,
        "zone_delay": 2,
        "is_active": True
})
l = []
print json.dumps(sm.get_jobs())
sm.remove_job(4)
for j in sm.get_jobs():
    l.append(j)

print sm.scheduler.get_jobs()[0].kwargs
"""
sched = ScheduleManager()
def execute(id, name, is_active, start_time, days, duration, zones, pre_zone, power_zone, zone_delay):
    logger = logging.getLogger(__name__)
    logger.info("Running execute for scheduled job ID #{} ({}) ".format(id, name))

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

    #if main, turn on
    if pre_led:
        logger.info("Turning on pre-zone")
        pre_led.on()
        sleep(zone_delay)

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



