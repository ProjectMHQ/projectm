from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.structcomponent import StructComponent


class InventoryComponent(StructComponent):
    component_enum = ComponentTypeEnum.INVENTORY
    key = ComponentTypeEnum.INVENTORY.value
    libname = "inventory"

    meta = (
        ("content", list),
        ("current_weight", int)
    )

    @classmethod
    def is_active(cls):
        return True
