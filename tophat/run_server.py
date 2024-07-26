from pathlib import Path

import board

from tophat.api.server import TopHatServer
from tophat.devices.neopixel import NeopixelDeviceProxy
from tophat.devices.printer import PrinterDevice


def main() -> None:
    server = TopHatServer(Path('/srv/tophat/test.socket'))
    server.register_device(PrinterDevice)
    server.register_device(NeopixelDeviceProxy, board.D12, 60)
    server.start()


if __name__ == '__main__':
    main()
