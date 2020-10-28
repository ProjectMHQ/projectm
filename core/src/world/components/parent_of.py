import typing
from core.src.world.components.base import ComponentTypeEnum, ComponentType
from core.src.world.components.base.listcomponent import ListComponent


class ParentOfComponent(ListComponent):
    enum = ComponentTypeEnum.PARENT_OF
    key = ComponentTypeEnum.PARENT_OF.value
    libname = "parent_of"
    subtype = int

    def __init__(self, *a, entity=None, entity_id=None, location: typing.Optional[ComponentType] = None):
        assert bool(entity or entity_id) == bool(location)
        if a and isinstance(a[0], list):
            value = [self.subtype(a[0][0]), self.subtype(a[0][1])]
        elif entity and location:
            entity_id = (entity and entity.entity_id) or entity_id
            value = [entity_id, location.enum]
        else:
            value = None
        super().__init__(value)

    @property
    def parent_id(self):
        return self._value[0]

    @property
    def location(self):
        return self._value[1]

    @classmethod
    def is_array(cls):
        return False
