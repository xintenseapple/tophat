from __future__ import annotations

from pathlib import Path

from tophat.api.client import TopHatClient
from tophat.devices.neopixel import RainbowCommand
from tophat.devices.printer import PrintCommand

client: TopHatClient = TopHatClient(Path('/srv/tophat/test.socket'))

client.send_command('printer', PrintCommand('HELLO WORLD'))

client.send_command('neopixels', RainbowCommand(15))
