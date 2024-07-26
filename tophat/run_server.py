from pathlib import Path

import board
import neopixel

from tophat.api.server import TopHatServer
from tophat.devices.neopixel import NeopixelDevice
from tophat.devices.printerdevice import PrinterDevice


def main() -> None:
    server = TopHatServer(Path('/srv/tophat/test.socket'))
    server.register_device(PrinterDevice, 0x1)
    server.register_device(NeopixelDevice, 0x2, neopixel.NeoPixel(board.D12, 60))
    server.start()


if __name__ == '__main__':
    main()
