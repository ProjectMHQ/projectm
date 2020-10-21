from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.intcomponent import IntComponent


class InstanceByComponent(IntComponent):
    component_enum = ComponentTypeEnum.INSTANCE_BY
    key = ComponentTypeEnum.INSTANCE_BY.value
    libname = "instance_by"
