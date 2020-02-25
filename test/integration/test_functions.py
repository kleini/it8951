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
    'partial_update'
]

import logging
import time
from PIL import Image, ImageDraw, ImageFont
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
    start = time.time()
    display.clear()
    logging.info('Clearing display took {:1.2f} seconds.'.format(time.time() - start))


def display_gradient(display):
    logging.info('Displaying gradient...')
    start = time.time()

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
    logging.info('Displaying gradient took {:1.2f} seconds.'.format(time.time() - start))


def display_image_8bpp(display):
    img_path = 'images/EWAe800-600.png'
    logging.info('Displaying "{}"...'.format(img_path))
    start = time.time()

    # clearing image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    img = Image.open(img_path)

    # TODO: this should be built-in
    dims = (display.width, display.height)

    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    display.frame_buf.paste(img, paste_coords)

    display.draw_full(constants.DisplayModes.GC16)
    logging.info('Displaying "{}" took {:1.2f} seconds.'.format(img_path, time.time() - start))


def partial_update(display):
    logging.info('Starting partial update...')

    # clear image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    logging.info('  writing full...')
    _place_text(display.frame_buf, 'partial', x_offset=-200)
    display.draw_full(constants.DisplayModes.GC16)

    # TODO: should use 1bpp for partial text update
    logging.info('  writing partial...')
    start = time.time()
    _place_text(display.frame_buf, 'update', x_offset=+200)
    display.draw_partial(constants.DisplayModes.DU)
    logging.info('Partial update took {:1.2f} seconds.'.format(time.time() - start))


# this function is just a helper for the others
def _place_text(img, text, x_offset=0, y_offset=0):
    """
    Put some centered text at a location on the image.
    """
    fontsize = 80

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('fonts/FreeSans.ttf', fontsize)

    img_width, img_height = img.size
    text_width, _ = font.getsize(text)
    text_height = fontsize

    draw_x = (img_width - text_width)//2 + x_offset
    draw_y = (img_height - text_height)//2 + y_offset

    draw.text((draw_x, draw_y), text, font=font)
