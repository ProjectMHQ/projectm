import typing

from core.src.world.components import ComponentType
from core.src.world.world_types import Transport

EntityID = typing.NewType('EntityID', int)


class Entity:
    def __init__(self, entity_id: typing.Optional[EntityID] = None, transport: Transport = None):
        self._entity_id = entity_id
        self._pending_changes = {}
        self.transport = transport

    async def emit_msg(self, payload: typing.Dict):
        return await self.transport.transport.emit(self.transport.namespace, 'msg', payload)

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
