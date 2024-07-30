from __future__ import annotations

import abc
import enum
from typing import Generic, Optional, Type

from typing_extensions import Self, final, override

from tophat.api.device import Command, DeviceType, ResultType

MAX_SEND_RECV_SIZE: int = 4096


class Message(abc.ABC):
    pass


class Request(Message, abc.ABC):
    pass


@final
class ResponseCode(enum.IntEnum):
    SUCCESS = enum.auto()
    ERROR_INVALID_DEVICE = enum.auto()
    ERROR_UNSUPPORTED_COMMAND = enum.auto()
    ERROR_UNKNOWN = enum.auto()


class Response(Message, abc.ABC):

    @final
    @property
    def code(self: Self) -> ResponseCode:
        return self._code

    @override
    def __init__(self,
                 code: ResponseCode) -> None:
        self._code: ResponseCode = code


@final
class CommandRequest(Generic[DeviceType, ResultType], Request):

    @property
    def device_name(self: Self) -> str:
        return self._device_name

    @property
    def command(self: Self) -> Command[DeviceType, ResultType]:
        return self._command

    @override
    def __init__(self,
                 device_name: str,
                 command: Command[DeviceType, ResultType]):
        self._command: Command[DeviceType, ResultType] = command
        self._device_name: str = device_name


@final
class CommandResponse(Generic[ResultType], Response):

    @property
    def result(self: Self) -> Optional[ResultType]:
        return self._result

    @classmethod
    def from_success(cls: Type[Self],
                     result: ResultType) -> Self:
        return cls(ResponseCode.SUCCESS, result)

    @classmethod
    def from_error(cls: Type[Self],
                   code: ResponseCode) -> Self:
        assert code is not ResponseCode.SUCCESS
        return cls(code, None)

    @override
    def __init__(self,
                 code: ResponseCode,
                 result: Optional[ResultType]) -> None:
        super().__init__(code)
        self._result: Optional[ResultType] = result
