import logging

from . import constants
from .constants import Commands, Registers, PixelModes
from .spi import SPI

from time import sleep

import numpy as np


class EPD:
    """
    An interface to the electronic paper display (EPD).

    Parameters
    ----------

    vcom : float
         The VCOM voltage that produces optimal display. Varies from
         device to device.
    """

    def __init__(self, vcom=-1.5):

        self.spi = SPI()

        self.width = None
        self.height = None
        self.img_buf_address = None
        self.img_buf_address = None
        self.firmware_version = None
        self.lut_version = None
        self.update_system_info()

        self._set_img_buf_base_addr(self.img_buf_address)

        # enable I80 packed mode
        self.write_register(Registers.I80CPCR, 0x1)
        # data = self.read_register(Registers.I80CPCR)
        # logging.debug(data)

        if vcom != self.get_vcom():
            self.set_vcom(vcom)
        # time.sleep(0.01)
        # logging.debug('Vcom = {:1.2f}'.format(self.get_vcom()))

    def load_img_area(self, buf, rotate_mode=constants.Rotate.NONE, xy=None, dims=None):
        """
        Write the pixel data in buf (an array of bytes, 1 per pixel) to device memory.
        This function does not actually display the image (see EPD.display_area).

        Parameters
        ----------

        buf : bytes
            An array of bytes containing the pixel data

        rotate_mode : constants.Rotate, optional
            A rotation mode for the data to be pasted into device memory

        xy : (int, int), optional
            The x,y coordinates of the top-left corner of the area being pasted. If omitted,
            the image is assumed to be the whole display area.

        dims : (int, int), optional
            The dimensions of the area being pasted. If xy is omitted (or set to None), the
            dimensions are assumed to be the dimensions of the display area.
        """

        endian_type = constants.EndianTypes.LITTLE
        pixel_format = constants.PixelModes.M_4BPP

        if xy is None:
            self._load_img_start(endian_type, pixel_format, rotate_mode)
        else:
            self._load_img_area_start(endian_type, pixel_format, rotate_mode, xy, dims)

        buf = self._pack_pixels(buf, pixel_format)
        self.spi.write_pixels(buf)

#        self._load_img_end()

    def update_system_info(self):
        """
        Get information about the system, and store it in class attributes
        """
        self.spi.write_cmd(Commands.GET_DEV_INFO, True)
        data = self.spi.read_data(20)
        self.width = data[0]
        self.height = data[1]
        self.img_buf_address = data[3] << 16 | data[2]
        self.firmware_version = ''.join([chr(x >> 8)+chr(x & 0xFF) for x in data[4:12]])
        self.lut_version = ''.join([chr(x >> 8)+chr(x & 0xFF) for x in data[12:20]])

    def get_vcom(self):
        """
        Get the device's current value for VCOM voltage
        """
        # Getting Vcom results in three rising edges of the busy line. This method currently reads only two of them.
        self.spi.write_cmd(Commands.VCOM, True, 0)
        vcom_int = self.spi.read_int()
        # logging.debug('get vcom end')
        return -vcom_int/1000

    def set_vcom(self, vcom):
        """
        Set the device's VCOM voltage
        """
        self._validate_vcom(vcom)
        vcom_int = int(-1000*vcom)
        # Setting Vcom results in three rising edges of the busy line. This method currently reads only one of them.
        self.spi.write_cmd(Commands.VCOM, True, 1, vcom_int)

    @staticmethod
    def _validate_vcom(vcom):
        # TODO: figure out the actual limits for vcom
        if not -5 < vcom < 0:
            raise ValueError("vcom must be between -5 and 0")

    @staticmethod
    def _pack_pixels(buf, pixel_format):
        """
        Take a buffer where each byte represents a pixel, and pack it
        into 16-bit words according to pixel_format.
        """
        buf = np.array(buf, dtype=np.ubyte)

        if pixel_format == PixelModes.M_8BPP:
            rtn = np.zeros((buf.size//2,), dtype=np.uint16)
            rtn |= buf[1::2]
            rtn <<= 8
            rtn |= buf[::2]

        elif pixel_format == PixelModes.M_2BPP:
            rtn = np.zeros((buf.size//8,), dtype=np.uint16)
            for i in range(7, -1, -1):
                rtn <<= 2
                rtn |= buf[i::8] >> 6

        elif pixel_format == PixelModes.M_3BPP:
            rtn = np.zeros((buf.size//4,), dtype=np.uint16)
            for i in range(3, -1, -1):
                rtn <<= 4
                rtn |= (buf[i::4] & 0xFE) >> 4

        elif pixel_format == PixelModes.M_4BPP:
            rtn = np.zeros((buf.size//4,), dtype=np.uint16)
            for i in range(3, -1, -1):
                rtn <<= 4
                rtn |= buf[i::4] >> 4

        else:
            rtn = None

        return rtn

    def wait_display_ready(self):
        while self.read_register(Registers.LUTAFSR):
            logging.debug('TODO Sleeping')
            sleep(0.01)

    def _load_img_start(self, endian_type, pixel_format, rotate_mode):
        arg = (endian_type << 8) | (pixel_format << 4) | rotate_mode
        self.spi.write_cmd(Commands.LD_IMG, arg)

    def _load_img_area_start(self, endian_type, pixel_format, rotate_mode, xy, dims):
        arg0 = (endian_type << 8) | (pixel_format << 4) | rotate_mode
        self.spi.write_cmd(Commands.LD_IMG_AREA, arg0, xy[0], xy[1], dims[0], dims[1])

    def read_register(self, address):
        """
        Read a device register
        """
        # logging.debug('read register start')
        self.spi.write_cmd(Commands.REG_RD, False, address)
        data = self.spi.read_int()
        # logging.debug('read register end')
        return data

    def write_register(self, address, val):
        """
        Write to a device register
        """
        # logging.debug('write register start')
        self.spi.write_cmd(Commands.REG_WR, True, address, val)
        # logging.debug('write register end')

    def _set_img_buf_base_addr(self, address):
        word0 = address >> 16
        word1 = address & 0xFFFF
        self.write_register(Registers.LISAR+2, word0)
        self.write_register(Registers.LISAR, word1)
        # logging.debug(self.read_register(Registers.LISAR+2))
        # logging.debug(self.read_register(Registers.LISAR))
