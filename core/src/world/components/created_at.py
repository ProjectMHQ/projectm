from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.intcomponent import IntComponent


class CreatedAtComponent(IntComponent):
    enum = ComponentTypeEnum.CREATED_AT
    key = ComponentTypeEnum.CREATED_AT.value
    libname = "created_at"
