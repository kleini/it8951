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
    'clear_display',
    'display_gradient',
    'sleep'
]

import logging
from time import sleep as sl

from sys import path
path += ['../../']
from IT8951 import constants


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


def display_gradient(display):
    print('Displaying gradient...')

    # set frame buffer to gradient
    for i in range(16):
        color = i * 0x10
        box = (
            i * display.width // 16,  # xmin
            0,  # ymin
            (i + 1) * display.width // 16,  # xmax
            display.height  # ymax
        )

        display.frame_buf.paste(color, box=box)

    # update display
    display.draw_full(constants.DisplayModes.GC16)


def sleep(display):
    sl(3)