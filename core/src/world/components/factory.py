from core.src.world.components import ComponentType, ComponentTypeEnum


def get_component_by_type(component_type_string) -> ComponentType:
    from core.src.world.components.attributes import AttributesComponent
    from core.src.world.components.character import CharacterComponent
    from core.src.world.components.connection import ConnectionComponent
    from core.src.world.components.created_at import CreatedAtComponent
    from core.src.world.components.instance_of import InstanceOfComponent
    from core.src.world.components.pos import PosComponent
    from core.src.world.components.weapon import WeaponComponent
    return {
        'attributes': AttributesComponent,
        'character': CharacterComponent,
        'connection': ConnectionComponent,
        'created_at': CreatedAtComponent,
        'instance_of': InstanceOfComponent,
        'pos': PosComponent,
        'weapon': WeaponComponent,
    }[component_type_string]


def get_component_alias_by_enum_value(enum_value: ComponentTypeEnum):
    return {
        ComponentTypeEnum.ATTRIBUTES: 'attributes',
        ComponentTypeEnum.CHARACTER: 'character',
        ComponentTypeEnum.CONNECTION: 'connection',
        ComponentTypeEnum.CREATED_AT: 'created_at',
        ComponentTypeEnum.INSTANCE_OF: 'instance_of',
        ComponentTypeEnum.POS: 'pos',
        ComponentTypeEnum.WEAPON: 'weapon'
    }[enum_value]
