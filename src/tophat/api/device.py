from __future__ import annotations

import abc
import multiprocessing.synchronize as mp_sync
from typing import Any, Callable, Generic, Set, Type, TypeVar

from typing_extensions import Concatenate, ParamSpec, Self, final, override

DeviceType = TypeVar('DeviceType', bound='Device')
ResultType = TypeVar('ResultType')
DeviceExtraParams = ParamSpec("DeviceImplParams")


@final
class UnsupportedCommandError(Exception):

    @override
    def __init__(self,
                 device: Device,
                 command: Command) -> None:
        super().__init__(f'Command {type(command)} not supported for device {device.name}')
        self._device = device
        self._command: Command = command


class DeviceBase(abc.ABC):

    @final
    @property
    def name(self: Self) -> str:
        return self._name

    @abc.abstractmethod
    def run(self: Self,
            lock: mp_sync.Lock,
            command: Command[DeviceType, ResultType]) -> ResultType:
        raise NotImplementedError()

    @classmethod
    @final
    def from_impl(cls: Type[Self],
                  device_name: str,
                  *args: DeviceExtraParams.args,
                  **kwargs: DeviceExtraParams.kwargs) -> Self:
        return cls._get_impl_builder()(device_name, *args, **kwargs)

    @classmethod
    @abc.abstractmethod
    def _get_impl_builder(cls: Type[Self]) -> Callable[Concatenate[str, DeviceExtraParams], Self]:
        raise NotImplementedError()

    @override
    def __init__(self,
                 device_name: str) -> None:
        self._name: str = device_name


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

    @classmethod
    @abc.abstractmethod
    def supported_commands(cls: Type[Self]) -> Set[Type[Command[Type[Self], Any]], ...]:
        raise NotImplementedError()

    @override
    def __init__(self,
                 device_name: str):
        super().__init__(device_name)


class DeviceProxy(Generic[DeviceType], DeviceBase, abc.ABC):

    @classmethod
    @final
    @override
    def _get_impl_builder(cls: Type[Self]) -> Callable[Concatenate[str, DeviceExtraParams], Self]:
        return cls


class Command(Generic[DeviceType, ResultType], abc.ABC):

    @abc.abstractmethod
    def run(self,
            device: DeviceType) -> ResultType:
        raise NotImplementedError()


class AsyncCommand(Command[DeviceType, None], abc.ABC):
    pass
