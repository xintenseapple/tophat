#!/bin/python3
from argparse import ArgumentParser
from pathlib import Path

import board

from tophat.devices.neopixel.proxy import DEFAULT_SOCKET_PATH, NeopixelServer

if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('socket_path',
                            type=Path)
    arg_parser.add_argument('pin',
                            type=int)
    arg_parser.add_argument('num_leds',
                            type=int)

    args = arg_parser.parse_args()
    server: NeopixelServer = NeopixelServer(DEFAULT_SOCKET_PATH, board.Pin(args.pin), args.num_leds)
