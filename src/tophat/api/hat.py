import abc

from typing_extensions import Self, override


class HackableHat(abc.ABC):

    @property
    @abc.abstractmethod
    def image_name(self: Self) -> str:
        raise NotImplementedError()

    @override
    def __init__(self):
        pass
