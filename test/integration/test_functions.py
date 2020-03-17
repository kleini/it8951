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
    'partial_update',
    'ewa'
]

import logging
import random
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
    paste_coords = [dims[i] - img.size[i] for i in (0, 1)]  # align image with bottom of display
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


def ewa(display):
    paper_display = PaperDisplay(display)
    start = time.time()
    #for i in range(0, 20):
        # paper_display.set_torque(random.uniform(0, 140))
    paper_display.set_torque(70)
    logging.debug('avg time {:1.3f}'.format((time.time() - start) / 20))
    time.sleep(5)
    paper_display.stop()


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

    draw_x = (img_width - text_width) // 2 + x_offset
    draw_y = (img_height - text_height) // 2 + y_offset

    draw.text((draw_x, draw_y), text, font=font)


from threading import Thread


class PaperDisplay(object):
    _run = True
    _torque = 0.0

    def __init__(self, display):
        self._display = display
        self._draw = ImageDraw.Draw(display.frame_buf)
        self._thread = Thread(target=self.display_loop, name='ePaper display loop')
        self._thread.start()

    def stop(self):
        self._run = False
        self._thread.join()

    def build(self):
        # general areas
        self._draw.rectangle([(0, 0), (268, 291)], 0xFF, 0x00, 5)
        self._draw.rectangle([(264, 0), (536, 291)], 0xFF, 0x00, 5)
        self._draw.rectangle([(532, 0), (799, 291)], 0xFF, 0x00, 5)
        self._draw.rectangle([(0, 309), (799, 599)], 0xFF, 0x00, 5)
        # battery
        self._draw.rectangle([(549, 39), (750, 107)], 0xFF, 0x00, 5)
        self._draw.rectangle([(746, 52), (763, 91)], 0xFF, 0x00, 5)
        self._draw.point([(549, 39), (750, 39), (549, 107), (750, 107), (763, 52), (763, 91)], 0xFF)
        self._draw.line([(554, 44), (745, 102)], 0x00, 5)
        # powerbar
        self._draw.rectangle([(16, 426), (745, 508)], 0xFF, 0x00, 3)
        self._draw.line([(746, 427), (782, 427)], 0x00, 3)
        self._draw.line([(746, 507), (782, 507)], 0x00, 3)
        self.draw_torque_lines()
        # texts top left
        self._draw.text((12, 8), 'EWA', font=ImageFont.truetype('fonts/Arial_Black.ttf', 48))
        font = ImageFont.truetype('fonts/Arial_Black.ttf', 32)
        self._draw.text((12, 75), 'Temperaturen', font=font)
        self._draw.text((12, 120), 'Motor', font=font)
        self._draw.text((12, 165), 'Controller', font=font)
        self._draw.text((12, 210), 'Batterie', font=font)
        self._draw.text((259 - font.getsize('28°')[0], 120), '28°', font=font)
        self._draw.text((259 - font.getsize('35°')[0], 165), '35°', font=font)
        self._draw.text((259 - font.getsize('46°')[0], 210), '46°', font=font)
        # texts top middle
        self._draw.text((282, 120), 'V Seil', font=font)
        self._draw.text((282, 165), '38 km/h', font=font)
        # texts top right
        self._draw.text((547, 120), 'Batterie', font=font)
        self._draw.text((547, 165), '78%', font=font)
        # texts in bottom box
        self._draw.text((16, 328), 'Zugkraft in kg', font=font)
        font27 = ImageFont.truetype('fonts/Arial_Black.ttf', 27)
        for i in list(range(0, 11)) + [13]:
            self._draw.text((16 + i * 56 - font27.getsize(str(i * 10))[0] / 2, 520), str(i * 10), font=font27)
        self._display.draw_full(constants.DisplayModes.GC16)

    def draw_torque_lines(self):
        for i in range(0, 14):
            self._draw.line([(16 + i * 56, 429), (16 + i * 56, 525)], 0x00)
        self._draw.line([(744, 426), (744, 508)], 0x00, 3)

    def set_torque(self, value):
        if value > 140:
            value = 140
        if value < 0:
            value = 0
        self._torque = value

    def draw_torque(self):
        right = self._torque * 5.6
        self._draw.rectangle([(19, 429), (794, 505)], 0xFF)
        if right > 794:
            right = 794
        if right > 3:
            self._draw.rectangle([(19, 429), (16 + right, 505)], 0x70)
        self.draw_torque_lines()
        self._display.draw_partial(constants.DisplayModes.GC16)

    def display_loop(self):
        self.build()
        while self._run:
            time.sleep(0.1)
