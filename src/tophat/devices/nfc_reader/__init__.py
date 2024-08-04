from __future__ import annotations

import abc
from typing import Any, Callable, Optional, Set, Type

from typing_extensions import Concatenate, Self, final, override

from tophat.api.device import Command, Device, DeviceExtraParams
from tophat.devices.nfc_reader.reader import ReaderProcess


class PN532Device(Device, abc.ABC):

    @abc.abstractmethod
    def read_data(self: Self,
                  timeout: Optional[float] = None) -> Optional[bytearray]:
        raise NotImplementedError()

    @classmethod
    @final
    @override
    def supported_commands(cls: Type[Self]) -> Set[Type[Command[Self, Any]]]:
        return {ReadDataCommand, }

    @classmethod
    @final
    @override
    def _get_impl_builder(cls: Type[Self]) -> Callable[Concatenate[str, DeviceExtraParams], Self]:
        from tophat.devices.nfc_reader._device_impl import PN532DeviceImpl
        return PN532DeviceImpl


class ReadDataCommand(Command[PN532Device, bytearray]):

    @override
    def run(self: Self,
            device: PN532Device) -> bytearray:
        return device.read_data(self._timeout)

    @override
    def __init__(self,
                 timeout: Optional[float] = None) -> None:
        self._timeout: Optional[float] = timeout
