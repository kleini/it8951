"""
This file contains various functions to test different aspects
of the module's display capabilities. Each function takes only
an AutoDisplay object (or, probably, an object of a type derived
from that class) as an argument, so they can be used with either
an actual AutoEPDDisplay, or a VirtualEPDDisplay, or something else.

See test.py for an example.
"""

# functions defined in this file
__all__ = [
    'print_system_info',
    'clear_display'
]

import logging


def print_system_info(display):
    epd = display.epd

    logging.info('System info:')
    logging.info('  Panel(W,H) = ({:d},{:d})'.format(epd.width, epd.height))
    logging.info('  Image Buffer Address = {:X}'.format(epd.img_buf_address))
    logging.info('  FW Version = {:s}'.format(epd.firmware_version))
    logging.info('  LUT Version = {:s}'.format(epd.lut_version))
    logging.info('')


def clear_display(display):
    print('Clearing display...')
    display.clear()
