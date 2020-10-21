from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.stringcomponent import StringComponent


class InstanceOfComponent(StringComponent):
    component_enum = ComponentTypeEnum.INSTANCE_OF
    key = ComponentTypeEnum.INSTANCE_OF.value
    libname = "instance_of"
