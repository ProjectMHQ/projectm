from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.stringcomponent import StringComponent


class ConnectionComponent(StringComponent):
    enum = ComponentTypeEnum.CONNECTION
    key = ComponentTypeEnum.CONNECTION.value
    libname = "connection"
