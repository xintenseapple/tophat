from __future__ import annotations

import abc
import multiprocessing.synchronize as mp_sync
from typing import Any, Generic, Tuple, Type, TypeVar

from typing_extensions import Self, final, override

DeviceType = TypeVar('DeviceType', bound='Device')
ResultType = TypeVar('ResultType')


@final
class UnsupportedCommandError(Exception):

    @override
    def __init__(self,
                 device: Device,
                 command: Command) -> None:
        super().__init__(f'Command {type(command)} not supported for device {device.id}')
        self._device = device
        self._command: Command = command


class DeviceBase(abc.ABC):

    @final
    @property
    def id(self) -> int:
        return self._id

    def __init__(self,
                 device_id: int) -> None:
        self._id: int = device_id


class Device(DeviceBase, abc.ABC):

    @final
    def run(self: Self,
            lock: mp_sync.Lock,
            command: Command[Self, ResultType]) -> ResultType:
        if type(command) in self.supported_commands():
            with lock:
                return command.run(self)
        else:
            raise UnsupportedCommandError(self, command)

    @override
    def __init__(self,
                 device_id: int):
        super().__init__(device_id)

    @classmethod
    @abc.abstractmethod
    def supported_commands(cls: Type[Self]) -> Tuple[Type[Command[Type[Self], Any]], ...]:
        raise NotImplementedError()


class DeviceProxy(Generic[DeviceType], DeviceBase, abc.ABC):

    @abc.abstractmethod
    def run(self: Self,
            lock: mp_sync.Lock,
            command: Command[DeviceType, ResultType]) -> ResultType:
        raise NotImplementedError()


class Command(Generic[DeviceType, ResultType], abc.ABC):

    @abc.abstractmethod
    def run(self,
            device: DeviceType) -> ResultType:
        raise NotImplementedError()


class AsyncCommand(Command[DeviceType, None], abc.ABC):
    pass
