from __future__ import annotations

from typing import (Iterable, Iterator, List, SupportsIndex, Union)

import board
import neopixel
from typing_extensions import Self, final, override

from tophat.devices.neopixel import ColorTuple, NeopixelDevice


@final
class NeopixelDeviceImpl(NeopixelDevice):

    @override
    def fill(self: Self,
             color: ColorTuple):
        self._pixels.fill(color)

    @override
    def show(self: Self):
        self._pixels.show()

    @override
    def __init__(self,
                 device_name: str,
                 pin: board.pin.Pin,
                 num_leds: int) -> None:
        super().__init__(device_name)
        self._pixels: neopixel.NeoPixel = neopixel.NeoPixel(pin, num_leds)

    @override
    def __getitem__(self,
                    item: Union[SupportsIndex, slice]) -> Union[ColorTuple, List[ColorTuple]]:
        return self._pixels[item]

    @override
    def __setitem__(self,
                    key: Union[SupportsIndex, slice],
                    value: Union[ColorTuple, Iterable[ColorTuple]]) -> None:
        self._pixels[key] = value

    @override
    def __len__(self) -> int:
        return len(self._pixels)

    @override
    def __iter__(self) -> Iterator[ColorTuple]:
        return iter(self._pixels)
