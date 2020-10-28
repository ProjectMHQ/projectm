from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.structcomponent import StructComponent


class InventoryComponent(StructComponent):
    enum = ComponentTypeEnum.INVENTORY
    libname = "inventory"

    meta = (
        ("content", list),
        ("current_weight", int)
    )
