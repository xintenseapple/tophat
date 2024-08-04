from time import sleep
from typing import Any, Set, Tuple, Type, final

from typing_extensions import Self, override

from tophat.api.device import AsyncCommand, Command, Device


@final
class PrinterDevice(Device):

    def print(self: Self,
              output: str) -> None:
        print(output)

    @classmethod
    @override
    def supported_commands(cls: Type[Self]) -> Set[Type[Command[Self, Any]]]:
        return {PrintCommand,}


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
