import typing

from core.src.world.components import ComponentType, ComponentTypeEnum


def get_component_by_type(component_type_string) -> typing.Type[ComponentType]:
    from core.src.world.components.attributes import AttributesComponent
    from core.src.world.components.character import CharacterComponent
    from core.src.world.components.connection import ConnectionComponent
    from core.src.world.components.created_at import CreatedAtComponent
    from core.src.world.components.instance_of import InstanceOfComponent
    from core.src.world.components.pos import PosComponent
    from core.src.world.components.weapon import WeaponComponent
    from core.src.world.components.inventory import InventoryComponent
    from core.src.world.components.parent_of import ParentOfComponent
    from core.src.world.components.instance_by import InstanceByComponent
    return {
        'attributes': AttributesComponent,
        'character': CharacterComponent,
        'connection': ConnectionComponent,
        'created_at': CreatedAtComponent,
        'instance_of': InstanceOfComponent,
        'pos': PosComponent,
        'weapon': WeaponComponent,
        'inventory': InventoryComponent,
        'parent_of': ParentOfComponent,
        'instance_by': InstanceByComponent
    }[component_type_string]


def get_component_alias_by_enum_value(enum_value: ComponentTypeEnum):
    return {
        ComponentTypeEnum.ATTRIBUTES: 'attributes',
        ComponentTypeEnum.CHARACTER: 'character',
        ComponentTypeEnum.CONNECTION: 'connection',
        ComponentTypeEnum.CREATED_AT: 'created_at',
        ComponentTypeEnum.INSTANCE_OF: 'instance_of',
        ComponentTypeEnum.POS: 'pos',
        ComponentTypeEnum.WEAPON: 'weapon',
        ComponentTypeEnum.INVENTORY: 'inventory',
        ComponentTypeEnum.PARENT_OF: 'parent_of',
        ComponentTypeEnum.INSTANCE_BY: 'instance_by'
    }[enum_value]


def get_component_by_enum_value(enum_value: ComponentTypeEnum):
    from core.src.world.components.attributes import AttributesComponent
    from core.src.world.components.character import CharacterComponent
    from core.src.world.components.connection import ConnectionComponent
    from core.src.world.components.created_at import CreatedAtComponent
    from core.src.world.components.instance_of import InstanceOfComponent
    from core.src.world.components.pos import PosComponent
    from core.src.world.components.weapon import WeaponComponent
    from core.src.world.components.inventory import InventoryComponent
    from core.src.world.components.parent_of import ParentOfComponent
    from core.src.world.components.instance_by import InstanceByComponent
    return {
        ComponentTypeEnum.ATTRIBUTES: AttributesComponent,
        ComponentTypeEnum.CHARACTER: CharacterComponent,
        ComponentTypeEnum.CONNECTION: ConnectionComponent,
        ComponentTypeEnum.CREATED_AT: CreatedAtComponent,
        ComponentTypeEnum.INSTANCE_OF: InstanceOfComponent,
        ComponentTypeEnum.POS: PosComponent,
        ComponentTypeEnum.WEAPON: WeaponComponent,
        ComponentTypeEnum.INVENTORY: InventoryComponent,
        ComponentTypeEnum.PARENT_OF: ParentOfComponent,
        ComponentTypeEnum.INSTANCE_BY: InstanceByComponent
    }[enum_value]
