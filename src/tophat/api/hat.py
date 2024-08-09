from __future__ import annotations

import abc
from typing import Any, Dict

from typing_extensions import Self, override


class HackableHat(abc.ABC):

    @property
    @abc.abstractmethod
    def image_name(self: Self) -> str:
        raise NotImplementedError()

    @property
    def extra_docker_args(self: Self) -> Dict[str, Any]:
        return {}

    @override
    def __init__(self):
        pass
