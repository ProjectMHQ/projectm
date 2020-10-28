from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.boolcomponent import BoolComponent


class CharacterComponent(BoolComponent):
    enum = ComponentTypeEnum.CHARACTER
    key = ComponentTypeEnum.CHARACTER.value
    libname = "character"
