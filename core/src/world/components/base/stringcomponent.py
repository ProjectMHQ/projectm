import typing

from core.src.world.components.base import ComponentType


class StringComponent(ComponentType):
    component_enum = NotImplementedError
    key = NotImplementedError
    component_type = str
    libname = NotImplementedError

    def __init__(self, value: str):
        super().__init__(value)

    @property
    def value(self) -> typing.Optional[str]:
        return self._value
