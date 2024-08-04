from __future__ import annotations

import board
from digitalio import DigitalInOut
from typing_extensions import Self, final, override

from tophat.devices.digital_switch import DigitalSwitchDevice


@final
class DigitalSwitchDeviceImpl(DigitalSwitchDevice):

    @property
    @override
    def state(self: Self) -> bool:
        return self._digital_io.value

    @state.setter
    @override
    def state(self: Self,
              value: bool) -> None:
        self._digital_io.value = value

    @override
    def __init__(self,
                 device_name: str,
                 pin: board.pin.Pin) -> None:
        super().__init__(device_name)
        self._digital_io = DigitalInOut(pin)
