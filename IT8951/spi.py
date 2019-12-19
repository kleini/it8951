import logging
from time import sleep

from .constants import Pins

import RPi.GPIO as GPIO


class SPI:

    def __init__(self):
        import spidev

        self.ready = False

        self.spi = spidev.SpiDev(0, 1)
        self.spi.max_speed_hz = 4000000  # maximum 12MHz
        self.spi.mode = 0b00

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        GPIO.setup(Pins.HRDY, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(Pins.RESET, GPIO.OUT, initial=GPIO.HIGH)

        GPIO.add_event_detect(Pins.HRDY, GPIO.RISING, self.ready_pin)

        # reset
        # logging.debug('Reset')
        GPIO.output(Pins.RESET, GPIO.LOW)
        sleep(0.1)
        self.prime_ready()
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

    def prime_ready(self):
        # logging.debug('prime ready')
        self.ready = False

    def wait_ready(self):
        """
        Wait for the device's ready pin to be set
        """
        # logging.debug('wait ready')
        timeout = 500
        while timeout > 0:
            timeout -= 1
            if self.ready:
                return
            # TODO passively wait for value to change
            sleep(0.01)
        logging.debug('timeout')
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

        send = [preamble]

        # spec says to read two dummy bytes, therefore count + 1
        for i in range(count + 1):
            send.append(0)

        self.prime_ready()
        data = self.xfer3(send)
        self.wait_ready()

        return data[2:]

    def write(self, preamble, ary):
        """
        Send preamble, and then write the data in ary (16-bit unsigned ints) over SPI
        """

        send = [preamble]

        if ary:
            send = send + ary

        self.xfer3(send)

    def write_pixels(self, pixbuf):
        """
        Write the pixels in pixbuf to the device. Pixbuf should be an array of
        16-bit ints, containing packed pixel information.
        """
        # FIXME

    def write_cmd(self, cmd, wait, *args):
        """
        Send the device a command code

        Parameters
        ----------

        cmd : int (from constants.Commands)
            The command to send

        wait : bool, optional
            True to wait for device to become ready. Set this only to false

        args : list(int), optional
            Arguments for the command
        """
        if wait:
            self.prime_ready()
        self.write(0x6000, [cmd])  # 0x6000 is preamble
        # between command and data chip select must toggle one time
        data = []
        for arg in args:
            data.append(arg)
        if data:
            self.write(0x0000, data)
            # self.write_data(data)
        if wait:
            self.wait_ready()

        # def write_data(self, ary):
        """
        Send the device an array of data

        Parameters
        ----------

        ary : array-like
            The data
        """
        # self.write(0x0000, ary)

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

    def xfer3(self, data):
        # logging.debug('transfer start')
        data = self.bytes2unsignedshort(self.spi.xfer3(self.unsignedshort2bytes(data)))
        # logging.debug('transfer end')
        return data

    @staticmethod
    def unsignedshort2bytes(data):
        retval = [None] * (len(data) * 2)
        for i in range(0, len(data)):
            retval[i * 2] = data[i] >> 8
            retval[i * 2 + 1] = data[i] & 0xFF
        return retval

    @staticmethod
    def bytes2unsignedshort(data):
        retval = [None] * (len(data) // 2)
        for i in range(0, len(data) // 2):
            retval[i] = (data[i * 2] << 8) + data[i * 2 + 1]
        return retval
