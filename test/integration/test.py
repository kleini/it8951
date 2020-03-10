import logging
import sys
import time

from test_functions import *


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')

    from sys import path
    path += ['../../']

    tests = []

    if not False:
        from IT8951.display import AutoEPDDisplay

#        logging.info('Initializing EPD...')
        display = AutoEPDDisplay()
        time.sleep(0.1)
#        logging.info('VCOM set to {:1.2f}'.format(display.epd.get_vcom()))

    tests += [
#        print_system_info,
        ewa
    ]

    for t in tests:
        t(display)

#    logging.info('Done!')

    return 0


if __name__ == '__main__':
    sys.exit(main())
