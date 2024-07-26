from pathlib import Path

from tophat.api.server import TopHatServer
from tophat.devices.printer import Printer


def main() -> None:
    server = TopHatServer(Path('/srv/tophat/test.socket'))
    server.register_device(Printer, 0x1)
    server.start()


if __name__ == '__main__':
    main()
