from __future__ import annotations

import sys
from pathlib import Path

from adafruit_platformdetect import Detector

from tophat.devices.digital_switch import DigitalSwitchDevice

if Detector().board.any_raspberry_pi_40_pin:
    import adafruit_blinka.board.raspberrypi.raspi_40pin as board
else:
    print('Cannot run server on non-rpi device', file=sys.stderr)
    exit(-1)

from tophat.api.server import TopHatServer
from tophat.devices.neopixel import NeopixelDeviceProxy
from tophat.devices.nfc_reader import PN532Device


def main() -> None:
    server = TopHatServer(Path('/srv/tophat/tophat.socket'))
    server.register_device(NeopixelDeviceProxy,
                           'neopixels',
                           Path('/srv/tophat/neopixel.socket'))
    server.register_device(PN532Device,
                           'nfc_reader',
                           board.SCK, board.MOSI, board.MISO, board.D25,
                           server.manager).start_reader()
    server.register_device(DigitalSwitchDevice,
                           'headlamp',
                           board.D23)

    server.start()


if __name__ == '__main__':
    main()
