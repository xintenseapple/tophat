from __future__ import annotations

import contextlib
import dataclasses
import itertools
import multiprocessing.synchronize as mp_sync
import signal
import time
from types import FrameType, TracebackType
from typing import (Any, Callable, Generator, Iterable, Iterator, List, Optional, Sequence, SupportsIndex, Tuple, Type,
                    TypeVar, Union)

import neopixel
from typing_extensions import Self, final, overload, override

from tophat.api.device import AsyncCommand, Command, Device

ExceptionType = TypeVar("ExceptionType",
                        bound=BaseException)

ColorTuple = Tuple[int, int, int]


@final
@dataclasses.dataclass(frozen=True, order=True, slots=True)
class Color:
    # Fields
    red: int
    green: int
    blue: int

    def as_neopixel(self: Self) -> ColorTuple:
        return self.red, self.green, self.blue

    @classmethod
    def from_neopixel(cls: Type[Self],
                      color: ColorTuple) -> Self:
        return cls(*color)

    @classmethod
    def get_blank(cls: Type[Self]) -> Self:
        return cls(0, 0, 0)

    @classmethod
    def get_red(cls: Type[Self]) -> Self:
        return cls(255, 0, 0)

    @classmethod
    def get_green(cls: Type[Self]) -> Self:
        return cls(0, 255, 0)

    @classmethod
    def get_blue(cls: Type[Self]) -> Self:
        return cls(0, 0, 255)

    @override
    def __str__(self):
        return f'({self.red}, {self.green}, {self.blue})'


@final
class Duration(contextlib.AbstractContextManager):
    class _TimedOutError(Exception):
        pass

    def _timeout_handler(self: Self,
                         signum: int,
                         frame: FrameType):
        raise Duration._TimedOutError()

    @override
    def __init__(self,
                 duration: int) -> None:
        self._duration: int = duration

    @override
    def __enter__(self: Self) -> Self:
        self._original_sigalrm_handler: Optional[Callable] = signal.getsignal(signal.SIGALRM)

        if self._duration > 0:
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self._duration)

        return self

    @override
    def __exit__(self: Self,
                 exc_type: Optional[Type[ExceptionType]],
                 exc_val: Optional[ExceptionType],
                 exc_tb: Optional[TracebackType]) -> bool:
        # Cancel any existing alarm
        signal.alarm(0)

        # Reset SIGALRM handler
        signal.signal(signal.SIGALRM, self._original_sigalrm_handler)

        return exc_type is None or exc_type == Duration._TimedOutError


@final
class NeopixelDevice(Device, Sequence[ColorTuple]):

    def fill(self,
             color: Color):
        self._pixels.fill(color.as_neopixel())

    def show(self):
        self._pixels.show()

    @classmethod
    @override
    def _valid_commands(cls: Type[Self]) -> Tuple[Type[Command[Self, Any]], ...]:
        return SolidColorCommand, BlinkCommand, PulseCommand, RainbowCommand, RainbowWaveCommand

    @override
    def __init__(self,
                 lock: mp_sync.Lock,
                 device_id: int,
                 pixels: neopixel.NeoPixel) -> None:
        super().__init__(lock, device_id)
        self._pixels: neopixel.NeoPixel = pixels

    @overload
    def __getitem__(self,
                    item: SupportsIndex) -> ColorTuple:
        ...

    @overload
    def __getitem__(self,
                    item: slice) -> List[ColorTuple]:
        ...

    @override
    def __getitem__(self,
                    item: Union[SupportsIndex, slice]) -> Union[ColorTuple, List[ColorTuple]]:
        return self._pixels[item]

    @overload
    def __setitem__(self,
                    key: SupportsIndex,
                    value: Color) -> None:
        ...

    @overload
    def __setitem__(self,
                    key: slice,
                    value: Iterable[Color]) -> None:
        ...

    def __setitem__(self,
                    key: Union[SupportsIndex, slice],
                    value: Union[Color, Iterable[Color]]) -> None:
        self._pixels[key] = value.as_neopixel()

    @override
    def __len__(self) -> int:
        return len(self._pixels)

    @override
    def __iter__(self) -> Iterator[Color]:
        return iter(map(Color.from_neopixel, iter(self._pixels)))


@final
class SolidColorCommand(AsyncCommand[NeopixelDevice]):

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        device.fill(self._color)
        device.show()

    @override
    def __init__(self,
                 color: Color) -> None:
        self._color: Color = color


@final
class BlinkCommand(AsyncCommand[NeopixelDevice]):

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        with Duration(self._duration):
            while True:
                device.fill(self._color)
                device.show()
                time.sleep(1 / self._frequency / 2)

                device.fill(Color.get_blank())
                time.sleep(1 / self._frequency / 2)

    @override
    def __init__(self,
                 duration: int,
                 color: Color,
                 frequency: int = 2) -> None:
        self._duration: int = duration
        self._color: Color = color
        self._frequency: int = frequency


@final
class PulseCommand(AsyncCommand[NeopixelDevice]):

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        with Duration(self._duration):
            for i in itertools.chain(range(0, 1000, 1), range(999, 0, -1)):
                device.brightness = i / 1000
                device.show()
                time.sleep(1 / self._frequency / 1000 / 2)

    @override
    def __init__(self,
                 duration: int,
                 color: Color,
                 frequency: int = 2,
                 blanks: int = 0) -> None:
        self._duration: int = duration
        self._color: Color = color
        self._frequency: int = frequency
        self._blanks: int = blanks


_CycleGenerator = Generator[int, None, None]


def _cycle_generator(min_val: int = 0,
                     max_val: int = 255,
                     steps: int = 1,
                     blanks: int = 0) -> _CycleGenerator:
    bounded_min = max(0, min_val)
    bounded_max = min(max_val, 255)
    bounded_steps = max(0, steps)
    assert bounded_max > bounded_min

    yield from itertools.cycle(itertools.chain(range(bounded_min, bounded_max, bounded_steps),
                                               range(bounded_max, bounded_min - 1, -bounded_steps),
                                               (0,) * blanks))


_ColorGenerator = Generator[Color, None, None]


def _rainbow_generator(start: int = 0) -> _ColorGenerator:
    bounded_start: int = max(min(start, 765), 0)

    red_start: int = bounded_start
    green_start: int = (bounded_start + 255) % 765
    blue_start: int = (bounded_start + (255 * 2)) % 765

    red = itertools.islice(_cycle_generator(blanks=255), red_start, None)
    green = itertools.islice(_cycle_generator(blanks=255), green_start, None)
    blue = itertools.islice(_cycle_generator(blanks=255), blue_start, None)

    while True:
        yield Color(next(red), next(green), next(blue))


@final
class RainbowCommand(AsyncCommand[NeopixelDevice]):

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        with Duration(self._duration):
            for color in _rainbow_generator():
                device.fill(color)
                device.show()
                time.sleep(1 / self._frequency)

    @override
    def __init__(self,
                 duration: int,
                 frequency: int = 10) -> None:
        self._duration: int = duration
        self._frequency: int = frequency


@final
class RainbowWaveCommand(AsyncCommand[NeopixelDevice]):

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        num_pixels: int = len(device)
        start_offset: int = 765 // num_pixels

        color_generators: Tuple[_ColorGenerator, ...] = tuple(_rainbow_generator(start=start_offset * i)
                                                              for i
                                                              in range(0, num_pixels))
        with Duration(self._duration):
            time.sleep(1 / self._frequency)
            for i in range(0, num_pixels):
                device[i] = next(color_generators[i])

    @override
    def __init__(self,
                 duration: int,
                 frequency: int = 10) -> None:
        super().__init__()
        self._duration: int = duration
        self._frequency: int = frequency
