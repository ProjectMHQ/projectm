from core.src.world.components.types import ComponentType, ComponentTypeEnum


class ConnectionComponent(ComponentType):
    key = ComponentTypeEnum.CONNECTION.value

    def __init__(self, value: str):
        self._value = value

    @property
    def value(self):
        return self._value
