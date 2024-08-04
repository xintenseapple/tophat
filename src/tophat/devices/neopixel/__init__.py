from __future__ import annotations

import abc
import contextlib
import dataclasses
import itertools
import json
import multiprocessing.synchronize as mp_sync
import signal
import socket
import time
from pathlib import Path
from types import FrameType, TracebackType
from typing import (Any, Callable, Dict, Generator, Iterable, Iterator, List, Optional, Sequence, Set, SupportsIndex,
                    Tuple, Type, TypeVar, Union)

from tophat.api.pin import Pin
import neopixel
from typing_extensions import Self, final, overload, override

from tophat.api.device import AsyncCommand, Device, DeviceProxy

ColorTuple = Tuple[int, int, int]
ExceptionType = TypeVar("ExceptionType",
                        bound=BaseException)


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
             color: ColorTuple):
        self._pixels.fill(color)

    def show(self):
        self._pixels.show()

    @classmethod
    @override
    def supported_commands(cls: Type[Self]) -> Set[Type[NeopixelCommand]]:
        return {SolidColorCommand, BlinkCommand, PulseCommand, RainbowCommand, RainbowWaveCommand}

    @override
    def __init__(self,
                 device_name: str,
                 pin: Pin,
                 num_leds: int) -> None:
        super().__init__(device_name)
        self._pixels: neopixel.NeoPixel = neopixel.NeoPixel(pin, num_leds)

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
                    value: ColorTuple) -> None:
        ...

    @overload
    def __setitem__(self,
                    key: slice,
                    value: Iterable[ColorTuple]) -> None:
        ...

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


@final
class NeopixelDeviceProxy(DeviceProxy[NeopixelDevice]):

    @override
    def run(self: Self,
            lock: mp_sync.Lock,
            command: NeopixelCommand) -> None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(str(self._socket_path))
            client_socket.sendall(command.serialize())

    @override
    def __init__(self,
                 device_name: str,
                 socket_path: Path) -> None:
        super().__init__(device_name)
        self._socket_path: Path = socket_path


@dataclasses.dataclass(frozen=True, init=True)
class NeopixelCommand(AsyncCommand[NeopixelDevice], abc.ABC):

    @final
    def serialize(self: Self) -> bytes:
        serialized_data = {
            'command_type': type(self).__name__,
            'command_kwargs': {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}
        }
        return json.dumps(serialized_data).encode('utf-8')

    @classmethod
    @final
    def deserialize(cls: Type[Self],
                    data: bytes) -> NeopixelCommand:
        deserialized_data = json.loads(data.decode('utf-8'))
        command_type: str = deserialized_data['command_type']
        command_kwargs: Dict[str, Any] = deserialized_data['command_kwargs']
        for supported_command in NeopixelDevice.supported_commands():
            if supported_command.__name__ == command_type:
                return supported_command(**command_kwargs)


@final
@dataclasses.dataclass(frozen=True, init=True)
class SolidColorCommand(NeopixelCommand):
    color: ColorTuple

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        device.fill(self.color)
        device.show()


@final
@dataclasses.dataclass(frozen=True, init=True)
class BlinkCommand(NeopixelCommand):
    duration: int
    color: ColorTuple
    frequency: int = 2

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        with Duration(self.duration):
            while True:
                device.fill(self.color)
                device.show()
                time.sleep(1 / self.frequency / 2)

                device.fill((0, 0, 0))
                time.sleep(1 / self.frequency / 2)
        device.fill((0, 0, 0))
        device.show()


@final
@dataclasses.dataclass(frozen=True, init=True)
class PulseCommand(NeopixelCommand):
    duration: int
    color: ColorTuple
    frequency: int = 2
    blanks: int = 0

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        with Duration(self.duration):
            for i in itertools.chain(range(0, 1000, 1), range(999, 0, -1)):
                device.brightness = i / 1000
                device.show()
                time.sleep(1 / self.frequency / 1000 / 2)
        device.fill((0, 0, 0))
        device.show()


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


_ColorGenerator = Generator[ColorTuple, None, None]


def _rainbow_generator(start: int = 0) -> _ColorGenerator:
    bounded_start: int = max(min(start, 765), 0)

    red_start: int = bounded_start
    green_start: int = (bounded_start + 255) % 765
    blue_start: int = (bounded_start + (255 * 2)) % 765

    red = itertools.islice(_cycle_generator(blanks=255), red_start, None)
    green = itertools.islice(_cycle_generator(blanks=255), green_start, None)
    blue = itertools.islice(_cycle_generator(blanks=255), blue_start, None)

    while True:
        yield next(red), next(green), next(blue)


@final
@dataclasses.dataclass(frozen=True, init=True)
class RainbowCommand(NeopixelCommand):
    duration: int
    frequency: int = 200

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        with Duration(self.duration):
            for color in _rainbow_generator():
                device.fill(color)
                device.show()
                time.sleep(1 / self.frequency)
        device.fill((0, 0, 0))
        device.show()


@final
@dataclasses.dataclass(frozen=True, init=True)
class RainbowWaveCommand(NeopixelCommand):
    duration: int
    frequency: int = 10

    @override
    def run(self: Self,
            device: NeopixelDevice) -> None:
        num_pixels: int = len(device)
        start_offset: int = 765 // num_pixels

        color_generators: Tuple[_ColorGenerator, ...] = tuple(_rainbow_generator(start=start_offset * i)
                                                              for i
                                                              in range(0, num_pixels))
        with Duration(self.duration):
            time.sleep(1 / self.frequency)
            for i in range(0, num_pixels):
                device[i] = next(color_generators[i])
        device.fill((0, 0, 0))
        device.show()
