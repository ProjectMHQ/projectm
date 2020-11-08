import typing

from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.structcomponent import StructComponent


class PositionComponent(StructComponent):
    enum = ComponentTypeEnum.POSITION
    libname = "position"

    meta = (
        ("coord", str),
        ("parent_of", int)
    )
    indexes = (
        "coord",
    )

    def __init__(self, **kw):
        super().__init__(**kw)
        self._list_coordinates = []
        self.previous_position = None

    def add_previous_position(self, previous: 'PositionComponent'):
        self.previous_position = previous
        return self

    def _make_coordinates(self) -> typing.Optional[typing.List]:
        if not self._list_coordinates:
            if self.coord.value:
                self._list_coordinates = [int(val) for val in self.coord.value.split(',')]
                if len(self._list_coordinates) == 2:
                    self._list_coordinates.append(0)
        return self._list_coordinates

    def set_list_coordinates(self, coord):
        self.coord.set('{},{},{}'.format(coord[0], coord[1], coord[2]))
        self._list_coordinates = coord
        return self

    @property
    def list_coordinates(self):
        return self._make_coordinates()

    @property
    def x(self):
        coord = self._make_coordinates()
        return coord and coord[0] or None

    @property
    def y(self):
        coord = self._make_coordinates()
        return coord and coord[1] or None

    @property
    def z(self):
        coord = self._make_coordinates()
        return coord and coord[2] or None
