from __future__ import annotations

import abc
from typing import Any, Callable, Set, Type

from typing_extensions import Concatenate, Self, final, override

from tophat.api.device import AsyncCommand, Command, Device, DeviceExtraParams


class DigitalSwitchDevice(Device, abc.ABC):

    @property
    @abc.abstractmethod
    def state(self: Self) -> bool:
        raise NotImplementedError()

    @state.setter
    @abc.abstractmethod
    def state(self: Self,
              value: bool) -> None:
        raise NotImplementedError()

    @classmethod
    @final
    @override
    def supported_commands(cls: Type[Self]) -> Set[Type[Command[Self, Any]]]:
        return {EnableCommand, DisableCommand, ToggleCommand}

    @classmethod
    @final
    @override
    def _get_impl_builder(cls: Type[Self]) -> Callable[Concatenate[str, DeviceExtraParams], Self]:
        from tophat.devices.digital_switch._device_impl import DigitalSwitchDeviceImpl
        return DigitalSwitchDeviceImpl


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
