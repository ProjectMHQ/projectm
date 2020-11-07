from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.structcomponent import StructComponent


class AttributesComponent(StructComponent):
    enum = ComponentTypeEnum.ATTRIBUTES
    libname = "attributes"

    meta = (
        ('name', str),
        ('description', str),
        ('keyword', str),
        ('collectible', bool)
    )
    defaults = (
        'name', 'description', 'keyword', 'collectible'
    )
