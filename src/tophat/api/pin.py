from __future__ import annotations

import adafruit_platformdetect
from typing_extensions import Self, final, override

if adafruit_platformdetect.Detector().board.any_raspberry_pi_40_pin:
    import adafruit_blinka.board.raspberrypi.raspi_40pin as board

    Pin = board.pin.Pin
else:

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
