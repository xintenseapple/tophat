from __future__ import annotations

import multiprocessing as mp
from typing import Optional

import board
from typing_extensions import Self, final, override

from tophat.devices.nfc_reader import PN532Device
from tophat.devices.nfc_reader.reader import ReaderProcess


@final
class PN532DeviceImpl(PN532Device):

    @override
    def read_data(self: Self,
                  timeout: Optional[float] = None) -> Optional[bytearray]:
        return self._reader_process.read_buffer_queue.get(block=True,
                                                          timeout=timeout)

    @override
    def __init__(self,
                 device_name: str,
                 sck_pin: board.pin.Pin,
                 mosi_pin: board.pin.Pin,
                 miso_pin: board.pin.Pin,
                 cs_pin: board.pin.Pin) -> None:
        super().__init__(device_name)
        mp.set_start_method('spawn', force=True)
        self._reader_process = ReaderProcess(sck_pin, mosi_pin, miso_pin, cs_pin)
        self._reader_process.start()
