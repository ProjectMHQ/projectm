from core.src.world.components.base import ComponentType


class IntComponent(ComponentType):
    enum = NotImplementedError
    key = NotImplementedError
    component_type = int
    libname = NotImplementedError

    def __init__(self, value: int):
        super().__init__(value)

    @property
    def value(self) -> int:
        return self._value
