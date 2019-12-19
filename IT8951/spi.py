import logging
from time import sleep

from .constants import Pins

import RPi.GPIO as GPIO


class SPI:

    def __init__(self):
        import spidev

        self.spi = spidev.SpiDev(0, 1)
        self.spi.max_speed_hz = 4000000 # maximum 12MHz
        self.spi.mode = 0b00

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(Pins.HRDY, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(Pins.RESET, GPIO.OUT, initial=GPIO.HIGH)

        GPIO.add_event_detect(Pins.HRDY, GPIO.RISING, self.ready_pin)
        self.ready = False

        # reset
        GPIO.output(Pins.RESET, GPIO.LOW)
        sleep(0.1)
        GPIO.output(Pins.RESET, GPIO.HIGH)
        self.wait_ready()

    def __del__(self):
        logging.debug('Cleanup')
        GPIO.cleanup()
        self.spi.close()

    # noinspection PyUnusedLocal
    def ready_pin(self, channel):
        self.ready = True
        # logging.debug('detected {:d}'.format(channel, self.ready))

    def wait_ready(self):
        """
        Wait for the device's ready pin to be set
        """
        timeout = 500
        while timeout > 0:
            timeout -= 1
            if self.ready:
                return
            sleep(0.01)
        logging.debug('timeout')
        return
        # if GPIO.input(Pins.HRDY) == 1:
        #     logging.warn('not busy')
        #     return None
        # retval = GPIO.wait_for_edge(Pins.HRDY, GPIO.RISING, timeout=5000)
        # if retval is None:
        #     logging.warn('busy timeout')
        # return retval

    def read(self, preamble, count):
        """
        Send preamble, and return a buffer of 16-bit unsigned ints of length count
        containing the data received
        """
        # logging.debug('Read')
        send = [preamble]
        # spec says to read two dummy bytes, therefore count + 1
        for i in range(0, count + 1, 1):
            send.append(0)
        data = self.bytes2unsignedshort(self.spi.xfer3(self.unsignedshort2bytes(send)))
        # self.wait_ready()
        self.ready = False
        return data[2:]

    def write(self, preamble, ary):
        """
        Send preamble, and then write the data in ary (16-bit unsigned ints) over SPI
        """
        # logging.debug('Write {:d}'.format(preamble))
        send = [preamble]
        if ary:
            send = send + ary
        self.ready = False
        self.spi.xfer3(self.unsignedshort2bytes(send))
        # self.wait_ready()

    def write_cmd(self, cmd, wait=False, *args):
        """
        Send the device a command code

        Parameters
        ----------

        cmd : int (from constants.Commands)
            The command to send

        wait : bool, optional
            True to wait for device to become ready

        args : list(int), optional
            Arguments for the command
        """
        self.write(0x6000, [cmd])  # 0x6000 is preamble
        # between command and data chip select must toggle one time
        for arg in args:
            self.write_data([arg])
        if wait:
            self.wait_ready()

    def write_data(self, ary):
        """
        Send the device an array of data

        Parameters
        ----------

        ary : array-like
            The data
        """
        self.write(0x0000, ary)

    def read_data(self, n):
        """
        Read n 16-bit words of data from the device

        Parameters
        ----------

        n : int
            The number of 2-byte words to read
        """
        return self.read(0x1000, n)

    def read_int(self):
        """
        Read a single 16 bit int from the device
        """
        return self.read_data(1)[0]

    @staticmethod
    def unsignedshort2bytes(data):
        retval = [None] * (len(data) * 2)
        for i in range(0, len(data)):
            retval[i*2] = data[i] >> 8
            retval[i*2+1] = data[i] & 0xFF
        return retval

    @staticmethod
    def bytes2unsignedshort(self, data):
        retval = [None] * (len(data) // 2)
        for i in range(0, len(data) // 2):
            retval[i] = (data[i*2] << 8) + data[i*2+1]
        return retval
