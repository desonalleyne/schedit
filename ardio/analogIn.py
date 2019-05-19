from nanpy import ArduinoApi, SerialManager
arduino = ArduinoApi(connection=SerialManager())

class AnalogIn():
    def __init__(self, pin, name=None):
        self.pin = pin
        arduino.pinMode(self.pin, arduino.INPUT)
        if name:
            self.name = name
        else:
            self.name = "Pin {}".format(pin)

    def read(self):
        return arduino.analogRead(self.pin)
        
