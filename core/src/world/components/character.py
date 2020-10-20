from core.src.world.components._types_ import ComponentTypeEnum
from core.src.world.components.base.boolcomponent import BoolComponent


class CharacterComponent(BoolComponent):
    component_enum = ComponentTypeEnum.CHARACTER
    key = ComponentTypeEnum.CHARACTER.value
    libname = "character"
