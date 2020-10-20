from core.src.world.components._types_ import ComponentTypeEnum
from core.src.world.components.base.listcomponent import ListComponent


class InventoryComponent(ListComponent):
    component_enum = ComponentTypeEnum.INVENTORY
    key = ComponentTypeEnum.INVENTORY.value
    libname = "inventory"
    subtype = int
