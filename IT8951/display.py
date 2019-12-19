from .interface import EPD


class AutoDisplay:
    pass


class AutoEPDDisplay(AutoDisplay):
    def __init__(self, epd=None, vcom=-2.06):
        if epd is None:
            epd = EPD(vcom=vcom)
        self.epd = epd
        AutoDisplay.__init__(self)
