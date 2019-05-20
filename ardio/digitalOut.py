from nanpy import ArduinoApi, SerialManager
arduino = ArduinoApi(connection=SerialManager())
from time import sleep
import logging

logger = logging.getLogger(__name__)


class DigitalOut(object):
    states = ["OFF", "ON"]

    def __init__(self, pin, name="name", pinType=None, id=None):
        logger.debug("pin:{0}, name:{1}, pinType:{2}".format(
            pin, name, pinType))
        self.pin = pin
        self.state = self.getState()
        self.stateString = self.getStateString()
        arduino.pinMode(pin, arduino.OUTPUT)
        if pinType == None:
            pinType = self.__class__.__name__

        self.name = "{} Pin ({}, {})".format(name, pinType, pin)

        # print "Initializating {}".format(self.name)

    def off(self):
        arduino.digitalWrite(self.pin, arduino.LOW)
        self.state = False
        logger.debug("{} turned {}".format(
            self.getName(), self.getStateString()))

    def on(self):
        arduino.digitalWrite(self.pin, arduino.HIGH)
        self.state = True
        logger.debug("{} turned {}".format(
            self.getName(), self.getStateString()))

    def toggle(self):
        if self.state == arduino.LOW:
            self.state = arduino.HIGH
        else:
            self.state = arduino.LOW
        arduino.digitalWrite(self.pin, self.state)
        print "{} toggled {}".format(self.name, self.getStateString())

    def dim(self, dimVal):
        arduino.analogWrite(self.pin, dimVal)
        self.state = dimVal

    def getState(self):
        return arduino.digitalRead(self.pin)

    def getStateString(self):
        return self.states[self.state]

    def setState(self, state):
        arduino.digitalWrite(self.pin, state)
        self.state = state

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name

# s = DigitalOut(3, "myname")
# s.on()
# sleep(5)
# s.off()
