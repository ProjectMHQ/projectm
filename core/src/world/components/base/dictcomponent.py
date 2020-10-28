import json
from ast import literal_eval
import typing
from core.src.world.components.base import ComponentType


class DictComponent(ComponentType):
    component_type = dict
    enum = NotImplementedError
    key = NotImplementedError
    libname = NotImplementedError

    @classmethod
    def from_bytes(cls, data: bytes):
        assert data
        return cls(literal_eval(data.decode()))

    def __init__(self, value: dict = None):
        value = value if value else dict()
        super().__init__(value)
        self._prev_pos = None
        self._component_values = {
            'name', 'description', 'keyword'
        }

    def __str__(self):
        return str(self.value)

    @property
    def value(self) -> typing.List[dict]:
        return self._value

    @property
    def serialized(self):
        return json.dumps(self.value)
