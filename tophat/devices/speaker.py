from typing import Any, Tuple, Type

from typing_extensions import Self, final

from tophat.api.device import Command, Device


@final
class SpeakerDevice(Device):

    @classmethod
    def supported_commands(cls: Type[Self]) -> Tuple[Type[Command[Self, Any]], ...]:
        pass