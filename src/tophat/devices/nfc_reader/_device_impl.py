from __future__ import annotations

import multiprocessing as mp
import multiprocessing.queues as mp_queue
import time
from typing import Optional

import board
from adafruit_pn532.adafruit_pn532 import PN532
from adafruit_pn532.spi import PN532_SPI
from busio import SPI
from digitalio import DigitalInOut
from typing_extensions import Self, final, override

from tophat.devices.nfc_reader import PN532Device


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


@final
class ReaderProcess(mp.Process):

    @property
    def read_buffer_queue(self: Self) -> mp_queue.Queue[bytearray]:
        return self._read_buffer_queue

    def stop(self: Self) -> None:
        self._stop_event.set()

    @override
    def run(self: Self) -> None:
        pn532: PN532 = PN532_SPI(spi=SPI(self._sck_pin, self._mosi_pin, self._miso_pin),
                                 cs_pin=DigitalInOut(self._cs_pin))
        pn532.low_power = True
        pn532.SAM_configuration()
        while True:
            try:
                self._read_buffer_queue.put(self._await_data(pn532))
            except ReaderProcess._Stopped:
                self._stop(pn532)

    @override
    def __init__(self,
                 sck_pin: board.pin.Pin,
                 mosi_pin: board.pin.Pin,
                 miso_pin: board.pin.Pin,
                 cs_pin: board.pin.Pin) -> None:
        super().__init__(name='nfc_reader',
                         daemon=True)
        self._sck_pin: board.pin.Pin = sck_pin
        self._mosi_pin: board.pin.Pin = mosi_pin
        self._miso_pin: board.pin.Pin = miso_pin
        self._cs_pin: board.pin.Pin = cs_pin

        self._read_buffer_queue: mp_queue.Queue[bytearray] = mp.Queue(maxsize=64)
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
        block_num: int = 4  # Start at block 4, beginning of user data
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