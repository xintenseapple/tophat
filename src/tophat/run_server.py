from pathlib import Path

import adafruit_blinka.board.raspberrypi.raspi_40pin as board

from tophat.api.server import TopHatServer
from tophat.devices.neopixel import NeopixelDeviceProxy
from tophat.devices.nfc_reader import PN532Device
from tophat.devices.printer import PrinterDevice


def main() -> None:
    server = TopHatServer(Path('/srv/tophat/test.socket'))
    server.register_device(PrinterDevice,
                           'printer')
    server.register_device(NeopixelDeviceProxy,
                           'neopixels',
                           Path('/srv/tophat/neopixel.socket'))
    server.register_device(PN532Device,
                           'nfc_reader',
                           board.SCK, board.MOSI, board.MISO, board.D25)
    server.start()


if __name__ == '__main__':
    main()
