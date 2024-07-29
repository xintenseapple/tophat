from __future__ import annotations

import multiprocessing as mp
from typing import Any, Optional, Tuple, Type

import board
from digitalio import DigitalInOut
from typing_extensions import Self, final, override

from tophat.api.device import Command, Device
from tophat.devices.nfc_reader.reader import ReaderProcess


@final
class PN532Device(Device):

    def read_data(self: Self,
                  timeout: Optional[float] = None) -> Optional[bytearray]:
        return self._reader_process.read_buffer_queue.get(block=True,
                                                          timeout=timeout)

    @classmethod
    @override
    def supported_commands(cls: Type[Self]) -> Tuple[Type[Command[Self, Any]], ...]:
        return (ReadDataCommand,)

    @override
    def __init__(self,
                 device_name: str,
                 sck: board.pin.Pin,
                 miso: board.pin.Pin,
                 mosi: board.pin.Pin,
                 cs: board.pin.Pin) -> None:
        super().__init__(device_name)
        mp.set_start_method('spawn')
        self._reader_process = ReaderProcess(sck, miso, mosi, cs)
        self._reader_process.start()


class ReadDataCommand(Command[PN532Device, bytearray]):

    @override
    def run(self: Self,
            device: PN532Device) -> bytearray:
        return device.read_data(self._timeout)

    @override
    def __init__(self,
                 timeout: Optional[float] = None) -> None:
        self._timeout: Optional[float] = timeout
