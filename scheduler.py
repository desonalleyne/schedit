#!/usr/bin/python
from job import Job 
import json
from time import sleep
from datetime import datetime, timedelta
import os
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from ardio import Led
logging.basicConfig(filename="/home/pi/projects/schedit/logs/schedit.log", format='[%(asctime)s] [%(levelname)s] %(name)s.%(funcName)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class Scheduler(object):
    def __init__(self):
        logger.info("SCHEDIT Starting up")
        self.jobs = []



    def add(self,days = None,
            id=1,
            start_time = None,
            duration = 0,
            beds = [],
            secondary_outputs = []):
            sched = Job(id=id,days=days, start_time=start_time, duration=duration,  beds=beds, secondary_outputs=secondary_outputs)

            self.jobs.append(sched)
    
    def load_configs(self, config):
        logger.info("Loading configs")
        with open(config) as file:
            data = file.read()
            data = json.loads(data)
            self.configs = data
            self.load_zones(data)
            self.load_jobs(data)

    def load_jobs(self,data):
        logger.info("Loading jobs")

        for job in data["jobs"]:
            j = Job(job)
            self.jobs.append(j)
        logger.info("Loading complete. {} jobs loaded.".format(len(self.jobs)))

    def load_zones(self,data):
        logger.info("Loading zones")
        self.zones = data["zones"]
        for zone in self.zones:
            z = Led(zone["pin"])
            z.off()
        logger.info("Loading complete. {} zones loaded.".format(len(self.jobs)))

    def edit(self,sched):
        return sched.update()

    def get_zone(self, id):
        for z in self.zones:
            if z["id"] == id:
                logger.debug("Zone {} found it".format(id))
                return z
        logger.error("Zone {} not found in config file!".format(id))
        return None

    def get_job(self, id):
        for s in self.jobs:
            if int(s.id) == id:
                logger.info("i found it")
                return s
        logger.info("Job {} not found".format(id))
        return None

    def get_jobs(self,active_only = False):
        if active_only:
            active_jobs = []
            for job in self.jobs:
                if job.is_active:
                    active_jobs.append(job)
            logger.info("active jobs: {}".format(str(len(active_jobs))))
            return active_jobs
        return self.jobs

def worker(id, name, is_active, start_time, days, duration, zones, pre_zone, power_zone, zone_delay):
    logger.info("Running worker for scheduled job ID #{} ({}) ".format(id, name))

    if pre_zone:
        _pre_zone = schedit.get_zone(pre_zone)
        pre_led = Led(_pre_zone["pin"], _pre_zone["name"])
        logger.warning("Pre-zone found.")
    else:
        logger.warning("No pre-zone found.")
        pre_led = None

    if power_zone:
        _power_zone = schedit.get_zone(power_zone)
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
        
        _zone = schedit.get_zone(zone)
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
        logger.info("Worker completed. Shutting down worker.")

        if power_led:
            power_led.off()
            sleep(zone_delay)

        zone_led.off()
        sleep(zone_delay)
        
    if pre_led:
        pre_led.off()
    
    logger.info("Yay! Job complete")
    """mainLed = Led(schedit.configs["main_valve_pin"], "main_valve")
    pump = Led(schedit.configs["pump_pin"], "pump")
    mainLed.on()
    sleep(1)
    for z in zones:
        led = Led(z, str(z))
        led.on()
        sleep(1)
        pump.on()
        sleep(duration)
        pump.off()
        led.off()
        #led.toggle()
    mainLed.off()
    """


if __name__ == '__main__':
    schedit = Scheduler()
    #schedit.jobs[0].update(days=1110011, start_time='11:11', duration = "5")
    schedit.load_configs("jobs.json")
    #print schedit.get_jobs()[0]o
    #job = schedit.get_job(1)

    scheduler = BlockingScheduler()
    for job in schedit.get_jobs(active_only=True):
        #print type(json.loads(str(job)))
#        job.start_time = str((datetime.now() + timedelta(seconds=6)).time())
        logger.info(str(job))
        #print type(eval(str(job)))
        logger.info("Scheduling job {}".format(job.id))
        hour = job.start_time[:2]
        minute = job.start_time[3:5]
        second = job.start_time[6:8]
        days = job.days
        #scheduler.add_job(worker, kwargs=json.loads(str(job)))
        #scheduler.add_job(worker, 'cron',  day_of_week=days, second='*/2', kwargs=json.loads(str(job)))
        scheduler.add_job(worker, 'cron',  day_of_week=days, hour=hour, minute=minute, second=second, kwargs=json.loads(str(job)))
        logger.warning("job scheduled")
        #scheduler.add_job(worker, 'interval', seconds=1, kwargs=eval(str(job)))

    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


