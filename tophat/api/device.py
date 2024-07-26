from __future__ import annotations

import abc
import multiprocessing as mp
import multiprocessing.synchronize as mp_sync
import socket
import uuid
from pathlib import Path
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


class Device(abc.ABC):

    @final
    @property
    def id(self) -> int:
        return self._id

    @final
    def run(self: Self,
            command: Command[Self, ResultType]) -> ResultType:
        if type(command) in self._valid_commands():
            with self._lock:
                return command.run(self)
        else:
            raise UnsupportedCommandError(self, command)

    @override
    def __init__(self,
                 lock: mp_sync.Lock,
                 device_id: int):
        self._id: int = device_id
        self._lock: mp_sync.Lock = lock

    @classmethod
    @abc.abstractmethod
    def _valid_commands(cls: Type[Self]) -> Tuple[Type[Command[Self, Any]], ...]:
        raise NotImplementedError()


@final
class DeviceProxy(Generic[DeviceType]):

    @property
    def id(self) -> int:
        return self._id

    def send(self,
             command: Command[DeviceType, ResultType]) -> ResultType:
        pass

    @override
    def __init__(self,
                 device_id: int,
                 tophat_socket_path: Path) -> None:
        self._id: int = device_id

        if not tophat_socket_path.is_socket():
            raise ValueError('tophat_socket_path is not a socket!')

        try:
            self._socket: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(str(tophat_socket_path))
        except OSError:
            print('Failed to connect to tophat server!')
            raise


class Command(Generic[DeviceType, ResultType], abc.ABC):

    @abc.abstractmethod
    def run(self,
            device: DeviceType) -> ResultType:
        raise NotImplementedError()


class AsyncCommand(Command[DeviceType, None], abc.ABC):
    pass
