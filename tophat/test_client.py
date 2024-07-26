from pathlib import Path

from tophat.api.client import TopHatClient
from tophat.devices.printer import PrintCommand

client: TopHatClient = TopHatClient(Path('/srv/tophat/test.socket'))

client.send_command(0x1, PrintCommand('HELLO WORLD'))
