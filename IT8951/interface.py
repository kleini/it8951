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
        [self.width, self.height, self.img_buf_address, self.firmware_version, self.lut_version] =\
            self.update_system_info()

        self._set_img_buf_base_addr(self.img_buf_address)

        # enable I80 packed mode
        self.write_register(Registers.I80CPCR, 0x1)
        # logging.debug(self.read_register(Registers.I80CPCR))

        # logging.debug('Vcom = {:1.2f}'.format(vcom))
        if vcom != self.get_vcom():
            self.set_vcom(vcom)
        # sleep(0.01)
        # logging.debug('Vcom = {:1.2f}'.format(self.get_vcom()))

    def __del__(self):
        # logging.debug('Ende EPD')
        self.spi.__del__()

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
        # logging.debug('pixels {:d}'.format(len(buf)))
        self.spi.count = 0
        self.spi.write_ndata(buf)
        # logging.debug('pixels done {:d}'.format(self.spi.count))

        self._load_img_end()

    def display_area(self, xy, dims, display_mode):
        """
        Update a portion of the display to whatever is currently stored in device memory
        for that region. Updated data can be written to device memory using EPD.write_img_area
        """
        self.spi.send_cmd_arg(Commands.DPY_AREA, [xy[0], xy[1], dims[0], dims[1], display_mode], 2.0)

    def update_system_info(self):
        """
        Get information about the system, and store it in class attributes
        """
        self.spi.write_cmd_code(Commands.GET_DEV_INFO, 1.0)
        data = self.spi.read_data(20)
        img_buf_address = data[2] | (data[3] << 16)
        firmware_version = ''.join([chr(x >> 8)+chr(x & 0xFF) for x in data[4:12]])
        lut_version = ''.join([chr(x >> 8)+chr(x & 0xFF) for x in data[12:20]])
        return data[0:2] + [img_buf_address, firmware_version, lut_version]

    def get_vcom(self):
        """
        Get the device's current value for VCOM voltage
        """
        self.spi.count = 0
        self.spi.write_cmd_code(Commands.VCOM, 1.0)
        self.spi.write_data(0)
        vcom_int = self.spi.read_int()
        return -vcom_int/1000

    def set_vcom(self, vcom):
        """
        Set the device's VCOM voltage
        """
        self._validate_vcom(vcom)
        self.spi.write_cmd_code(Commands.VCOM, 1.0)
        self.spi.write_data(1)
        self.spi.write_data(int(-1000*vcom))

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

        return rtn.tolist()

    def wait_display_ready(self):
        while self.read_register(Registers.LUTAFSR):
            logging.debug('LUTAFSR register says display is not ready')
            sleep(0.01)

    def _load_img_start(self, endian_type, pixel_format, rotate_mode):
        logging.debug('load_img_start')
        arg = (endian_type << 8) | (pixel_format << 4) | rotate_mode
        self.spi.write_cmd(Commands.LD_IMG, True, arg)

    def _load_img_area_start(self, endian_type, pixel_format, rotate_mode, xy, dims):
        arg0 = (endian_type << 8) | (pixel_format << 4) | rotate_mode
        self.spi.send_cmd_arg(Commands.LD_IMG_AREA, [arg0, xy[0], xy[1], dims[0], dims[1]])

    def _load_img_end(self):
        self.spi.write_cmd_code(Commands.LD_IMG_END)

    def read_register(self, address):
        """
        Read a device register
        """
        self.spi.write_cmd_code(Commands.REG_RD)
        self.spi.write_data(address, 0.0)
        return self.spi.read_int()

    def write_register(self, address, val):
        """
        Write to a device register
        """
        self.spi.write_cmd_code(Commands.REG_WR)
        self.spi.write_ndata([address, val])

    def _set_img_buf_base_addr(self, address):
        word_h = (address >> 16) & 0x0000FFFF
        word_l = address & 0x0000FFFF
        self.write_register(Registers.LISAR+2, word_h)
        self.write_register(Registers.LISAR, word_l)

    def active(self):
        self.spi.write_cmd_code(Commands.SYS_RUN, 1.0)

    def sleep(self):
        self.spi.write_cmd_code(Commands.SLEEP, 1.0)
