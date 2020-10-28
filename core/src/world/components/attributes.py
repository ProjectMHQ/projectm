from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.dictcomponent import DictComponent


class AttributesComponent(DictComponent):
    enum = ComponentTypeEnum.ATTRIBUTES
    key = ComponentTypeEnum.ATTRIBUTES.value
    libname = "attributes"
    has_default = True

    meta = (
        ('name', str),
        ('description', str),
        ('keyword', str),
    )

    @property
    def name(self):
        return self._value.get('name')

    @property
    def description(self):
        return self._value.get('description')

    @property
    def keyword(self):
        return self._value.get('keyword')
