from core.src.world.components import ComponentType


class BoolComponent(ComponentType):
    component_enum = NotImplementedError
    key = NotImplementedError
    component_type = bool
    libname = NotImplementedError

    def __init__(self, value: (int, bool) = None):
        if not isinstance(value, bool):
            assert value in (0, 1), value
            value = bool(value or 0)
        super().__init__(value)

    @property
    def value(self) -> bool:
        return self._value

    def as_int(self):
        return int(self._value)
