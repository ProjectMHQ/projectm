import typing
from core.src.world.components._types_ import ComponentTypeEnum
from core.src.world.components.base.listcomponent import ListComponent


class PosComponent(ListComponent):
    component_enum = ComponentTypeEnum.POS
    key = ComponentTypeEnum.POS.value
    libname = "pos"

    def __init__(self, value: (list, tuple) = None):
        if value is None:
            value = value
        elif value != list:
            value = list(value)
            if len(value) == 2:
                value.append(0)
        super().__init__(value)
        self._prev_pos = None

    def __str__(self):
        return 'x: {}, y:{}, z: {}'.format(self.x, self.y, self.z)

    @property
    def x(self):
        return self._value[0]

    @property
    def y(self):
        return self._value[1]

    @property
    def z(self):
        return self._value[2]

    def has_previous_position(self):
        return bool(self._prev_pos)

    def add_previous_position(self, position: 'PosComponent'):
        self._prev_pos = position
        return self

    @property
    def previous_position(self) -> typing.Optional['PosComponent']:
        return self._prev_pos

    @classmethod
    def is_array(cls):
        """
        Important, override this value because PosComponent is not treated as a normal array component.
        It MUST stay disabled.
        """
        return False
