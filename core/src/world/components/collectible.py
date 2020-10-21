from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.boolcomponent import BoolComponent


class CollectibleComponent(BoolComponent):
    component_enum = ComponentTypeEnum.COLLECTIBLE
    key = ComponentTypeEnum.COLLECTIBLE.value
    libname = "collectible"
    has_default = True
