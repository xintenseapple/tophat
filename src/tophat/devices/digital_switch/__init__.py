from __future__ import annotations

from typing import Any, Set, Type, final

from tophat.api.pin import Pin
from digitalio import DigitalInOut
from typing_extensions import Self, override

from tophat.api.device import AsyncCommand, Command, Device


@final
class DigitalSwitchDevice(Device):

    @property
    def state(self: Self) -> bool:
        return self._digital_io.value

    @state.setter
    def state(self: Self,
              value: bool) -> None:
        self._digital_io.value = value

    @classmethod
    @override
    def supported_commands(cls: Type[Self]) -> Set[Type[Command[Self, Any]]]:
        return {EnableCommand, DisableCommand, ToggleCommand}

    @override
    def __init__(self,
                 device_name: str,
                 pin: Pin) -> None:
        super().__init__(device_name)
        self._digital_io = DigitalInOut(pin)


@final
class EnableCommand(AsyncCommand[DigitalSwitchDevice]):

    @override
    def run(self: Self,
            device: DigitalSwitchDevice) -> None:
        device.state = True


@final
class DisableCommand(AsyncCommand[DigitalSwitchDevice]):

    @override
    def run(self: Self,
            device: DigitalSwitchDevice) -> None:
        device.state = False


@final
class ToggleCommand(AsyncCommand[DigitalSwitchDevice]):

    @override
    def run(self: Self,
            device: DigitalSwitchDevice) -> None:
        device.state = not device.state
