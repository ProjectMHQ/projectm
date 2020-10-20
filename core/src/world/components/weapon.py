from enum import Enum

from core.src.world.components._types_ import ComponentTypeEnum
from core.src.world.components.base.stringcomponent import StringComponent


class WeaponType(Enum):
    SWORD = 'sword'
    KNIFE = 'knife'
    BROADSWORD = 'broadsword'


class WeaponComponent(StringComponent):
    component_enum = ComponentTypeEnum.WEAPON
    key = ComponentTypeEnum.WEAPON.value
    libname = "weapon"
    has_default = True

    def __init__(self, value: str = None):
        super().__init__(value and WeaponType(value).value)

    @property
    def value(self) -> WeaponType:
        return self._value and WeaponType(self._value)
