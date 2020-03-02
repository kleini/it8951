import logging
import sys
from PIL import Image, ImageDraw
from test_functions import *

def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    frame_buf = Image.new('L', (800, 600), 0xFF)
    draw(frame_buf)
    frame_buf.save('test.png')


if __name__ == '__main__':
    sys.exit(main())
