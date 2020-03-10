import logging
import time
from threading import Event

from .constants import Pins

import RPi.GPIO as GPIO


class SPI:

    MAX_BUFFER_SIZE = 1024

    def __init__(self):
        import spidev

        self.ready = Event()
        self.debug = False
        self.count = 0

        self.spi = spidev.SpiDev(0, 1)
        # raising the frequency does not make data transfer faster
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
        time.sleep(0.1)
        self.prime_ready()
        GPIO.output(Pins.RESET, GPIO.HIGH)
        self.wait_ready(2.0)

    def __del__(self):
        GPIO.cleanup()
        self.spi.close()

    def ready_pin(self, channel):
        self.ready.set()
        self.count = self.count + 1
        if self.debug:
            logging.debug('detected {:d}'.format(channel))

    def prime_ready(self):
        self.ready.clear()

    def wait_ready(self, timeout=1.0):
        if timeout == 0.0:
            return
        start = time.time()
        if self.ready.wait(timeout):
            return
        logging.error('{:1.3f}'.format(time.time() - start))

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

    def write_ndata(self, data, timeout=1.0):
        for i in range(0, len(data), self.MAX_BUFFER_SIZE):
            end = i + self.MAX_BUFFER_SIZE
            if end > len(data):
                end = len(data)
            self.prime_ready()
            self.xfer3([0x0000] + data[i:end])
            self.wait_ready(timeout)

    def write_data(self, us_data, timeout=1.0):
        """
        Write a single data value to the controller.
        :param us_data: data value to sent.
        :param timeout: default 1.0 seconds
        """
        self.prime_ready()
        self.xfer3([0x0000, us_data])
        self.wait_ready(timeout)

    def write_cmd_code(self, cmd_code, timeout=0.0):
        """
        Write a command code to the controller.
        :param cmd_code: code to sent
        :param timeout: set value to non-zero to enable checking the interrupt line after sending the command code.
        """
        self.prime_ready()
        self.xfer3([0x6000, cmd_code])
        self.wait_ready(timeout)

    def send_cmd_arg(self, cmd_code, args, timeout=1.0):
        """
        Write a command code with arguments to the controller.
        :param cmd_code: command code to sent.
        :param args: arguments to sent.
        :param timeout: default 1.0 seconds
        """
        self.write_cmd_code(cmd_code)
        for arg in args:
            self.write_data(arg, timeout)

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
