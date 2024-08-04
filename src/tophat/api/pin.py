from __future__ import annotations

from typing_extensions import Self, final, override

try:
    import adafruit_blinka.board.raspberrypi.raspi_40pin as board

    Pin = board.pin.Pin

except ImportError:

    @final
    class Pin:

        @override
        def __init__(self,
                     bcm_number: int):
            self.id: int = bcm_number

        @override
        def __repr__(self: Self):
            return str(self.id)

        @override
        def __eq__(self: Self,
                   other: int):
            return self.id == other
