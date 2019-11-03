import typing

from core.src.world.components import ComponentType


EntityID = typing.NewType(
    'EntityID', int
)


class Entity:
    def __init__(self, entity_id: typing.Optional[EntityID] = None):
        self._entity_id = entity_id
        self._pending_changes = {}

    def set(self, component: ComponentType):
        self._pending_changes[component.key] = component
        return self

    @property
    def entity_id(self) -> EntityID:
        return EntityID(self._entity_id)

    @entity_id.setter
    def entity_id(self, value: EntityID):
        assert not self._entity_id
        self._entity_id = value

    @property
    def pending_changes(self):
        return self._pending_changes

    def get_values(self, *components: ComponentType, repository=None) \
            -> (None, str, int, list):
        if not repository:
            from core.src.world.builder import world_components_repository as repository
        data = repository.get_components_values(self.entity_id, *components)
        return (components[i](components[i].ctype(v)) for i, v in enumerate(data))
