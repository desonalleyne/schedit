from digitalOut import DigitalOut


class Led(DigitalOut):
    def __init__(self, pin, name="Unnamed", id=None):
        pinType = self.__class__.__name__
        super(Led, self).__init__(pin, name, pinType, id)

    def get_classname(self):
        return
