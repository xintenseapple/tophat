from __future__ import annotations

import argparse
import sys
from os import stat_result
from pathlib import Path

import board
from adafruit_pn532.adafruit_pn532 import PN532
from adafruit_pn532.spi import PN532_SPI
from busio import SPI
from digitalio import DigitalInOut

DEFAULT_SCK_PIN: board.pin.Pin = board.SCK
DEFAULT_MISO_PIN: board.pin.Pin = board.MISO
DEFAULT_MOSI_PIN: board.pin.Pin = board.MOSI
DEFAULT_CS_PIN: board.pin.Pin = board.D25
MAX_DATA_SIZE: int = 512

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sck',
                        type=board.pin.Pin,
                        default=DEFAULT_SCK_PIN)
    parser.add_argument('--mosi',
                        type=board.pin.Pin,
                        default=DEFAULT_MOSI_PIN)
    parser.add_argument('--miso',
                        type=board.pin.Pin,
                        default=DEFAULT_MISO_PIN)
    parser.add_argument('--cs',
                        type=board.pin.Pin,
                        default=DEFAULT_CS_PIN)
    parser.add_argument('file_path',
                        type=Path)

    args = parser.parse_args()

    file_path: Path = args.file_path
    if not file_path.is_file():
        print(f'Invalid input file {file_path}', file=sys.stderr)
        exit(1)

    file_stat: stat_result = file_path.lstat()
    if file_stat.st_size > MAX_DATA_SIZE:
        print(f'Input file of size {hex(file_stat.st_size)} is too large (max size is {hex(MAX_DATA_SIZE)})',
              file=sys.stderr)
        exit(2)

    file_data: bytes = file_path.read_bytes()

    pn532: PN532 = PN532_SPI(SPI(args.sck, args.mosi, args.miso), DigitalInOut(args.cs))
    pn532.SAM_configuration()

    while pn532.read_passive_target(timeout=0.5) is None:
        pass

    for index, file_data_block in enumerate(file_data[i:i + 4] for i in range(0, len(file_data), 4)):
        if not pn532.ntag2xx_write_block(index, file_data_block):
            print(f'Failed to write block {index}', file=sys.stderr)
            exit(3)

    pn532.power_down()
    print(f'Successfully wrote {hex(file_stat.st_size)} bytes to NFC card')
