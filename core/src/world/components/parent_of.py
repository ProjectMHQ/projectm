import typing
from core.src.world.components.base import ComponentTypeEnum, ComponentType
from core.src.world.components.base.listcomponent import ListComponent


class ParentOfComponent(ListComponent):
    component_enum = ComponentTypeEnum.PARENT_OF
    key = ComponentTypeEnum.PARENT_OF.value
    libname = "parent_of"
    subtype = int

    def __init__(self, entity=None, location: typing.Optional[ComponentType] = None):
        assert bool(entity) == bool(location)
        if entity and location:
            value = [entity.entity_id, location.component_enum]
        else:
            value = None
        super().__init__(value)

    @property
    def parent_id(self):
        return self._value[0]

    @property
    def location(self):
        return self._value[1]
