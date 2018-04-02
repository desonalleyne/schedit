#import dateparser
import time
import json
import logging

class Job(object):
    id = None
    days = None
    start_time = None
    duration = 0
    beds = []
    zones = []
    pre_zone = None
    power_zone = None
    zone_delay = None

    """def __init__(self,
            id = None,
            days = None,
            start_time = None,
            duration = 0,
            beds=[],
            secondary_outputs=[]
            ):
        self.id = id
        self.days = days
        self.start_time = start_time
        self.duration = duration
        self.beds = beds
        self.secondary_outputs = secondary_outputs
        for k, v in self.__dict__.iteritems():
            setattr(self, k, v)
        return self
    """
    def __init__(self, schedule):
        logger = logging.getLogger(__name__)
        logger.info("Creating job: {}".format(schedule["id"]))
        self._validate(schedule)

    def __iter__(self):
        return self
        

    def __str__(self):
        return json.dumps({"id": self.id,
                "name": self.name,
                "is_active": self.is_active,
                "days": self.days,
                "start_time":self.start_time,
                "duration": self.duration,
                "zones": self.zones,
                "pre_zone": self.pre_zone,
                "power_zone": self.power_zone,
                "zone_delay": self.zone_delay})
        
    def __dict__(self):
        return json.loads(json.dumps({"days": self.days,
                "start_time":self.start_time,
                "duration": self.duration,
                "beds": self.beds,
                "zones": self.zones,
                "secondary_outputs": self.secondary_outputs}))
    
    def create():
        pass

    def update(self, **changes):
        print "Updating schedule"
        #self.days = days
        #self.start_time = start_time
        #self.duration = duration
        self._validate(changes)
        logger.info("update completed")

    def _validate(self, kwargs):
        logger = logging.getLogger(__name__)
        logger.info("Validating values")
        approved = {}
        for k,v in kwargs.iteritems():
            if k == 'id' and self.id is None:
                approved[k] = v

            if k == 'name':
                approved[k] = v

            if k == 'is_active':
                approved[k] = v
            if k == 'days':
                """
                WIP. days in integer equivalent eg: 127 instead of 1111111
                if len(str(v)) < 7:
                    print "int parsing"
                    if v > 127 or v < 1:
                        print v
                        raise ValueError("'days' must be between 1 and 127 inclusive")
                    approved[k] = bin(v)[2:]
                    """

                try:
                #    tmp_list = v.split(",")
                 #   s = sum(int(x) for x in tmp_list)
                 #   if s > 7 or sum < 0:
                 ##       print "ve1"
                 #       raise ValueError("Use binary numbers")
                 #   if len(tmp_list) > 7:
                 #       print "ve2"
                 #       raise ValueError("not enough days supplied")

                    #int(str(v),base=2)
                    approved[k] = v
                except ValueError as e:
                    print str(e)
                    raise ValueError("Error: Invalid values entered for 'days'. Input must be in binary format")
            if k == 'start_time':
                try:
                    
                    #v = dateparser.parse(v).time()
                    approved[k] = str(v)
                except ValueError as e:
                    raise ValueError("Error: Bad time format for 'start_time'. Please use HH:MMH:SS")

            if k == 'duration':
                try:
                    v = int(v)
                    approved[k] = v
                except ValueError as e:
                    raise ValueError("duration must be an int")

            if k == 'pre_zone':
                approved[k] = v
            
            if k == 'power_zone':
                approved[k] = v
            
            if k == 'zones':
                approved[k] = v

            if k == 'zone_delay':
                approved[k] = v

        for k, v in approved.iteritems():
            setattr(self, k, v)



