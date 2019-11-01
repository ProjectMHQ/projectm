from core.src.world.components.types import ComponentType


class Entity:
    def __init__(self, entity_id: int = None):
        self._entity_id = entity_id
        self._pending_changes = {}
        self._changes_lock = None

    def set(self, component: ComponentType):
        self._pending_changes[component.key] = component.value

    @property
    def entity_id(self):
        return self.entity_id

    @entity_id.setter
    def entity_id(self, value: int):
        assert isinstance(value, int)
        assert not self._entity_id
        self._entity_id = value

    @property
    def pending_changes(self):
        return self._pending_changes
