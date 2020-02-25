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
    'display_image_8bpp',
]

import logging
from PIL import Image
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
    logging.info('Clearing display...')
    display.clear()


def display_gradient(display):
    logging.info('Displaying gradient...')

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


def display_image_8bpp(display):
    img_path = 'images/EWAe800-600.png'
    logging.info('Displaying "{}"...'.format(img_path))

    # clearing image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    img = Image.open(img_path)

    # TODO: this should be built-in
    dims = (display.width, display.height)

    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    display.frame_buf.paste(img, paste_coords)

    display.draw_full(constants.DisplayModes.GC16)
