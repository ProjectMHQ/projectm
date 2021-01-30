import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.abstract import ComponentType
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.position import PositionComponent
from core.src.world.components.system import SystemComponent


def get_component_by_type(component_type_string) -> typing.Type[ComponentType]:
    return {
        'attributes': AttributesComponent,
        'position': PositionComponent,
        'inventory': InventoryComponent,
        'system': SystemComponent
    }[component_type_string]


def get_component_alias_by_enum_value(enum_value: ComponentTypeEnum):
    return {
        ComponentTypeEnum.ATTRIBUTES: 'attributes',
        ComponentTypeEnum.SYSTEM: 'system',
        ComponentTypeEnum.POSITION: 'position',
        ComponentTypeEnum.INVENTORY: 'inventory',
    }[enum_value]


def get_component_by_enum_value(enum_value: ComponentTypeEnum):
    return {
        ComponentTypeEnum.ATTRIBUTES: AttributesComponent,
        ComponentTypeEnum.SYSTEM: SystemComponent,
        ComponentTypeEnum.POSITION: PositionComponent,
        ComponentTypeEnum.INVENTORY: InventoryComponent
    }[enum_value]
