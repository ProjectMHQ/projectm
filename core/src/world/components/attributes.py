from core.src.world.components._types_ import ComponentTypeEnum
from core.src.world.components.base.dictcomponent import DictComponent


class AttributesComponent(DictComponent):
    component_enum = ComponentTypeEnum.ATTRIBUTES
    key = ComponentTypeEnum.ATTRIBUTES.value
    libname = "attributes"
    has_default = True

    @property
    def name(self):
        return self._value.get('name')

    @property
    def description(self):
        return self._value.get('description')

    @property
    def keyword(self):
        return self._value.get('keyword')
