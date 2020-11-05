import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.base import ComponentType, ComponentTypeEnum
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.parent_of import ParentOfComponent
from core.src.world.components.pos import PosComponent
from core.src.world.components.system import SystemComponent
from core.src.world.components.weapon import WeaponComponent


def get_component_by_type(component_type_string) -> typing.Type[ComponentType]:
    return {
        'attributes': AttributesComponent,
        'pos': PosComponent,
        'weapon': WeaponComponent,
        'inventory': InventoryComponent,
        'parent_of': ParentOfComponent,
        'system': SystemComponent
    }[component_type_string]


def get_component_alias_by_enum_value(enum_value: ComponentTypeEnum):
    return {
        ComponentTypeEnum.ATTRIBUTES: 'attributes',
        ComponentTypeEnum.SYSTEM: 'system',
        ComponentTypeEnum.POS: 'pos',
        ComponentTypeEnum.WEAPON: 'weapon',
        ComponentTypeEnum.INVENTORY: 'inventory',
        ComponentTypeEnum.PARENT_OF: 'parent_of'
    }[enum_value]


def get_component_by_enum_value(enum_value: ComponentTypeEnum):
    return {
        ComponentTypeEnum.ATTRIBUTES: AttributesComponent,
        ComponentTypeEnum.SYSTEM: SystemComponent,
        ComponentTypeEnum.POS: PosComponent,
        ComponentTypeEnum.WEAPON: WeaponComponent,
        ComponentTypeEnum.INVENTORY: InventoryComponent,
        ComponentTypeEnum.PARENT_OF: ParentOfComponent,
    }[enum_value]
