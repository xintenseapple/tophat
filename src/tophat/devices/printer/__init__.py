from __future__ import annotations

from time import sleep
from typing import Any, Callable, Set, Type, final

from typing_extensions import Concatenate, Self, override

from tophat.api.device import AsyncCommand, Command, Device, DeviceExtraParams


@final
class PrinterDevice(Device):

    def print(self: Self,
              output: str) -> None:
        print(output)

    @classmethod
    @override
    def supported_commands(cls: Type[Self]) -> Set[Type[Command[Self, Any]]]:
        return {PrintCommand, }

    @classmethod
    @override
    def _get_impl_builder(cls: Type[Self]) -> Callable[Concatenate[str, DeviceExtraParams], Self]:
        return cls


class PrintCommand(AsyncCommand[PrinterDevice]):

    @override
    def run(self: Self,
            device: PrinterDevice) -> None:
        sleep(10)
        device.print(self._output)

    @override
    def __init__(self,
                 output: str) -> None:
        self._output: str = output
