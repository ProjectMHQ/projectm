from core.src.world.components.types import ComponentType, ComponentTypeEnum


class CreatedAtComponent(ComponentType):
    key = ComponentTypeEnum.CREATED_AT.value

    def __init__(self, value: int):
        self._value = value

    @property
    def value(self):
        return self._value
