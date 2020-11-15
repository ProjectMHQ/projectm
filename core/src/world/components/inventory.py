from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.structcomponent import StructComponent


class InventoryComponent(StructComponent):
    enum = ComponentTypeEnum.INVENTORY
    libname = "inventory"

    meta = (
        ("content", list),
        ("current_weight", int)
    )

    def __init__(self, **kw):
        super().__init__(**kw)
        self._raw_populated = []
        self._owner = None

    @property
    def populated(self):
        return self._raw_populated
