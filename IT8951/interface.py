import logging
import time

from .constants import Commands, Registers
from .spi import SPI


class EPD:

    def __init__(self, vcom=-1.5):

        self.spi = SPI()

        self.width = None
        self.height = None
        self.img_buf_address = None
        self.firmware_version = None
        self.lut_version = None
        self.img_buf_address = self.update_system_info()

        self._set_img_buf_base_addr(self.img_buf_address)

        # enable I80 packed mode
        self.write_register(Registers.I80CPCR, 0x1)
        # data = self.read_register(Registers.I80CPCR)
        # logging.debug(data)

        self.set_vcom(vcom)
        logging.debug(vcom)
        time.sleep(0.1)
        logging.debug(self.get_vcom())

    def update_system_info(self):
        """
        Get information about the system, and store it in class attributes
        """
        self.spi.write_cmd(Commands.GET_DEV_INFO, True)
        data = self.spi.read_data(20)
        # logging.debug(len(data))
        # logging.debug(data)
        self.width = data[0]
        self.height = data[1]
        logging.info('{:d} {:d}'.format(self.width, self.height))
        local_img_buf_address: int = data[3] << 16 | data[2]
        logging.info('{:d}'.format(self.img_buf_address))
        self.firmware_version = ''.join([chr(x >> 8)+chr(x & 0xFF) for x in data[4:12]])
        logging.info(self.firmware_version)
        self.lut_version = ''.join([chr(x >> 8)+chr(x & 0xFF) for x in data[12:20]])
        logging.info(self.lut_version)
        return local_img_buf_address

    def get_vcom(self):
        """
        Get the device's current value for VCOM voltage
        """
        self.spi.write_cmd(Commands.VCOM, True, 0)
        vcom_int = self.spi.read_int()
        return -vcom_int/1000

    def set_vcom(self, vcom):
        """
        Set the device's VCOM voltage
        """
        self._validate_vcom(vcom)
        vcom_int = int(-1000*vcom)
        self.spi.write_cmd(Commands.VCOM, True, 1, vcom_int)

    @staticmethod
    def _validate_vcom(vcom):
        # TODO: figure out the actual limits for vcom
        if not -5 < vcom < 0:
            raise ValueError("vcom must be between -5 and 0")

    def read_register(self, address):
        """
        Read a device register
        """
        self.spi.write_cmd(Commands.REG_RD, False, address)
        return self.spi.read_int()

    def write_register(self, address, val):
        """
        Write to a device register
        """
        self.spi.write_cmd(Commands.REG_WR, False, address)
        self.spi.write_data([val])

    def _set_img_buf_base_addr(self, address):
        word0 = address >> 16
        word1 = address & 0xFFFF
        self.write_register(Registers.LISAR+2, word0)
        logging.debug(word0)
        self.write_register(Registers.LISAR, word1)
        logging.debug(word1)
        data = self.read_register(Registers.LISAR+2)
        logging.debug(data)
        data = self.read_register(Registers.LISAR)
        logging.debug(data)
