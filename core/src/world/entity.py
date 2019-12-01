import typing

from core.src.world.components import ComponentType
from core.src.world.utils.world_types import Transport, EvaluatedEntity

EntityID = typing.NewType('EntityID', int)


class Entity:
    def __init__(self, entity_id: typing.Optional[EntityID] = None, transport: Transport = None):
        self._entity_id = entity_id
        self._pending_changes = {}
        self.transport = transport

    def get_view_size(self):
        return 15

    async def emit_msg(self, payload: typing.Dict, topic=None):
        if topic is not None:
            return await self.transport.transport.send(self.transport.namespace, payload, topic=topic)
        return await self.transport.transport.send(self.transport.namespace, payload)

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

    @staticmethod
    def can_see_evaluated_entity(evaluated_entity: EvaluatedEntity):
        # FIXME TODO
        return bool(evaluated_entity)
