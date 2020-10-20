from core.src.world.components._types_ import ComponentTypeEnum
from core.src.world.components.base.stringcomponent import StringComponent


class ConnectionComponent(StringComponent):
    component_enum = ComponentTypeEnum.CONNECTION
    key = ComponentTypeEnum.CONNECTION.value
    libname = "connection"
