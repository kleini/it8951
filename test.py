import logging
import sys


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')

#    data = [0x320, 0x1000, 0x6000]
#    #conv = struct.pack('>' + 'H' * len(data), *data)
#    logging.info(data)
#    #logging.info(conv)
#    logging.info(divmod(0x320, 1 << 8))
#    bytes = unsignedShort2Bytes(data)
#    logging.info(bytes)
#    logging.info(bytes2UnsignedShort(bytes))
#    return 0

    from IT8951.display import AutoEPDDisplay
    logging.info('Initializing EPD...')
    display = AutoEPDDisplay(vcom=-2.06)
    logging.info('Done!')

    return 0


if __name__ == '__main__':
    sys.exit(main())
