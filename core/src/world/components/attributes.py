from core.src.world.components.base.structcomponent import StructComponent


class AttributesComponent(StructComponent):

    meta = (
        ('name', str),
        ('description', str),
        ('keyword', str),
        ('collectible', bool)
    )
    defaults = (
        'name', 'description', 'keyword', 'collectible'
    )
