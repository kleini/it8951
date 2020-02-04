import logging
from threading import Event
from time import sleep

from .constants import Pins

import RPi.GPIO as GPIO


class SPI:

    def __init__(self):
        import spidev

        self.ready = False
        self.ready2 = Event()
        self.debug = False

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

    def ready_pin(self, channel):
        self.ready = True
        self.ready2.set()
        if self.debug:
            logging.debug('detected {:d}'.format(channel, self.ready))

    def prime_ready(self):
        # logging.debug('prime ready')
        self.ready = False

    def prime_ready2(self):
        self.ready2.clear()

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

    def wait_ready2(self, timeout=1.0):
        if self.ready2.wait(timeout):
            return
        logging.debug('timeout2')

    def read(self, preamble, count, debug=False):
        """
        Send preamble, and return a buffer of 16-bit unsigned ints of length count
        containing the data received
        """

        send = [preamble]

        # spec says to read two dummy bytes, therefore count + 1
        for i in range(count + 1):
            send.append(0)

        self.prime_ready()
        data = self.xfer3(send, debug)
        self.wait_ready()

        return data[2:]

    def write(self, preamble, ary):
        """
        Send preamble, and then write the data in ary (16-bit unsigned ints) over SPI
        """
        buf = [preamble]
        if ary:
            buf = buf + ary
        self.xfer3(buf)

    def write_pixels(self, pixbuf):
        """
        Write the pixels in pixbuf to the device. Pixbuf should be an array of
        16-bit ints, containing packed pixel information.
        """
        self.write(0x0000, pixbuf)

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
        self.write(0x6000, [cmd]) # 0x6000 is preamble
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

    def write_cmd_code(self, cmd_code):
        # Set Preamble for Write Command
        preamble = 0x6000

        # self.wait_ready()

        # CS low
        data = [0x6000, cmd_code]
        self.xfer3(data)

        # CS high

    def write_data(self, us_data, debug=False):
        # CS low
        buffer = [0x0000, us_data]
        if debug:
            logging.debug(buffer)
        self.prime_ready2()
        self.xfer3(buffer)
        self.wait_ready2(5.0)
        # CS high

    def send_cmd_arg(self, cmd_code, args, debug=False):
        self.write_cmd_code(cmd_code)
        for arg in args:
            self.write_data(arg, debug)

    def read_data(self, n, debug=False):
        """
        Read n 16-bit words of data from the device

        Parameters
        ----------

        n : int
            The number of 2-byte words to read
        debug: boolean
            True to debug received data
        """
        return self.read(0x1000, n, debug)

    def read_int(self):
        """
        Read a single 16 bit int from the device
        """
        return self.read_data(1)[0]

    def xfer3(self, data, debug=False):
        """
        Transfer 16-bit words of data to and from the device
        :param data: data to transfer to the device
        :param debug: True for debugging received data
        :return: data received from the device
        """
        # logging.debug('transfer start')
        tosend = self.unsignedshort2bytes(data)
        # for x in tosend:
        #     logging.debug(type(x))
        #     logging.debug(x)
        received = self.spi.xfer3(tosend)
        if debug:
            logging.debug(received)
        rtn = self.bytes2unsignedshort(received)
        # logging.debug('transfer end')
        return rtn

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
