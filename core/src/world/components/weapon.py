import typing
from enum import Enum

from core.src.world.components import ComponentType
from core.src.world.components.types import ComponentTypeEnum


class WeaponType(Enum):
    SWORD = 'sword'
    KNIFE = 'knife'
    BROADSWORD = 'broadsword'


class WeaponComponent(ComponentType):
    component_enum = ComponentTypeEnum.WEAPON
    key = ComponentTypeEnum.WEAPON.value
    component_type = str

    def __init__(self, value: str):
        super().__init__(value)

    @property
    def value(self) -> WeaponType:
        return WeaponType(self._value)

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['WeaponComponent']:
        return await super().get(entity_id, repo)
