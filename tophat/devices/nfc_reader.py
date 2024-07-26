from __future__ import annotations

import multiprocessing.synchronize as mp_sync
import multiprocessing as mp
import time
from typing import Any, Optional, Tuple, Type

from adafruit_pn532.spi import PN532_SPI
from adafruit_pn532.adafruit_pn532 import PN532
from busio import SPI
from digitalio import DigitalInOut
from typing_extensions import Self, final, override

from tophat.api.device import Command, Device


@final
class ReaderProcess(mp.Process):

    @property
    def read_buffer_queue(self: Self) -> mp.Queue[bytearray]:
        return self._read_buffer_queue

    def stop(self: Self) -> None:
        self._stop_event.set()

    @override
    def run(self: Self) -> None:
        pn532: PN532 = PN532_SPI(SPI(self._sck, self._mosi, self._miso), self._cs)
        pn532.low_power = True
        pn532.SAM_configuration()
        while True:
            try:
                self._queue.put(self._await_data(pn532))
            except ReaderProcess._Stopped:
                self._stop(pn532)

    @override
    def __init__(self,
                 cs: DigitalInOut,
                 sck: int,
                 mosi: int,
                 miso: int) -> None:
        super().__init__(name='nfc_reader',
                         daemon=True)
        self._cs = cs
        self._sck = sck
        self._mosi = mosi
        self._miso = miso

        self._read_buffer_queue: mp.Queue[bytearray] = mp.Queue[bytearray](maxsize=64)
        self._stop_event = mp.Event()

    class _Stopped(Exception):
        pass

    def _await_data(self: Self,
                    pn532: PN532) -> bytearray:
        while not self._stop_event.is_set():
            if pn532.listen_for_passive_target(timeout=0.2):
                break
            pn532.power_down()
            time.sleep(1.8)
        else:
            raise ReaderProcess._Stopped()

        return ReaderProcess._read_data(pn532)

    @staticmethod
    def _read_data(pn532: PN532) -> bytearray:
        data: bytearray = bytearray()
        block_num: int = 0
        block_data: Optional[bytearray] = pn532.ntag2xx_read_block(block_num)
        while block_data is not None:
            data += block_data
            block_num += 1
            block_data: Optional[bytearray] = pn532.ntag2xx_read_block(block_num)

        return data

    def _stop(self: Self,
              pn532: PN532) -> None:
        pn532.power_down()
        self._read_buffer_queue.close()
        self._read_buffer_queue.join_thread()


@final
class PN532Device(Device):

    def get_data(self: Self,
                 timeout: Optional[float] = None) -> Optional[bytearray]:
        return self._reader_process.read_buffer_queue.get(block=True,
                                                          timeout=timeout)

    @classmethod
    @override
    def supported_commands(cls: Type[Self]) -> Tuple[Type[Command[Self, Any]], ...]:
        return (ReadDataCommand,)

    @override
    def __init__(self,
                 device_id: int,
                 cs: DigitalInOut,
                 sck: int,
                 mosi: int,
                 miso: int) -> None:
        super().__init__(device_id)
        mp.set_start_method('spawn')
        self._reader_process = ReaderProcess(cs, sck, mosi, miso)
        self._reader_process.start()


class ReadDataCommand(Command[PN532Device, bytearray]):

    @override
    def run(self: Self,
            device: PN532Device) -> bytearray:
        return device.get_data(self._timeout)

    @override
    def __init__(self,
                 timeout: Optional[float] = None) -> None:
        self._timeout: Optional[float] = timeout
