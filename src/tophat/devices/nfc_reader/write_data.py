from __future__ import annotations

import argparse
import sys
from os import stat_result
from pathlib import Path

from adafruit_blinka.agnostic import detector

if detector.board.any_raspberry_pi_40_pin:
    import adafruit_blinka.board.raspberrypi.raspi_40pin as board
from adafruit_pn532.adafruit_pn532 import PN532, _COMMAND_SAMCONFIGURATION
from adafruit_pn532.spi import PN532_SPI
from busio import SPI
from digitalio import DigitalInOut

DEFAULT_SCK_PIN: int = board.SCK.id
DEFAULT_MISO_PIN: int = board.MISO.id
DEFAULT_MOSI_PIN: int = board.MOSI.id
DEFAULT_CS_PIN: int = board.D25.id
MAX_DATA_SIZE: int = 512

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sck',
                        type=int,
                        default=DEFAULT_SCK_PIN)
    parser.add_argument('--mosi',
                        type=int,
                        default=DEFAULT_MOSI_PIN)
    parser.add_argument('--miso',
                        type=int,
                        default=DEFAULT_MISO_PIN)
    parser.add_argument('--cs',
                        type=int,
                        default=DEFAULT_CS_PIN)
    parser.add_argument('--debug',
                        action='store_true',
                        default=False)
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

    sck_pin: board.pin.Pin = board.pin.Pin(args.sck)
    mosi_pin: board.pin.Pin = board.pin.Pin(args.mosi)
    miso_pin: board.pin.Pin = board.pin.Pin(args.miso)
    cs_pin: board.pin.Pin = board.pin.Pin(args.cs)
    pn532: PN532 = PN532_SPI(spi=SPI(sck_pin, mosi_pin, miso_pin),
                             cs_pin=DigitalInOut(cs_pin),
                             debug=args.debug)
    pn532.call_function(_COMMAND_SAMCONFIGURATION, params=[0x01, 0x00, 0x00])

    while pn532.read_passive_target(timeout=5) is None:
        pass

    for index, file_data_block in enumerate(file_data[i:i + 4] for i in range(0, len(file_data), 4)):
        block_num: int = index + 0x4
        if pn532.ntag2xx_write_block(block_num, file_data_block.ljust(4, b'\x00')):
            print(f'Successfully wrote block {block_num}')
        else:
            print(f'Failed to write block {block_num}', file=sys.stderr)
            exit(3)

    pn532.power_down()
    print(f'Successfully wrote {hex(file_stat.st_size)} bytes to NFC card')
