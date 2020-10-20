import typing

from core.src.world.components import ComponentType
from core.src.world.domain import DomainObject
from core.src.world.utils.world_types import Transport, EvaluatedEntity


class Entity(DomainObject):
    item_type = "entity"

    def __init__(self, entity_id: typing.Optional[int] = None, transport: Transport = None, itsme=False):
        self._entity_id = entity_id
        self._pending_changes = {}
        self.transport = transport
        self._bounds = []
        self._components = {}
        self._room = None
        self.itsme = itsme

    def set_room(self, room):
        self._room = room
        return self

    def get_room(self):
        return self._room

    def get_view_size(self):
        return 15

    async def disconnect_transport(self):
        await self.transport.transport.disconnect(namespace=self.transport.namespace)

    async def emit_msg(self, message: str):
        return await self.transport.transport.send_message(self.transport.namespace, message)

    async def emit_system_event(self, payload: typing.Dict):
        return await self.transport.transport.send_system_event(self.transport.namespace, payload)

    async def emit_system_message(self, event_type: str, item: DomainObject):
        assert isinstance(item, DomainObject)
        from core.src.world.utils.serialization import serialize_system_message_item
        item_type, details = serialize_system_message_item(item)
        payload = {
            "event_type": event_type,
            "target": item_type,
            "details": details
        }
        return await self.transport.transport.send_system_event(self.transport.namespace, payload)

    def set_for_update(self, component: ComponentType):
        self._pending_changes[component.key] = component
        return self

    @property
    def entity_id(self) -> int:
        return self._entity_id

    @entity_id.setter
    def entity_id(self, value: int):
        assert not self._entity_id
        self._entity_id = value

    @property
    def pending_changes(self):
        return self._pending_changes

    @staticmethod
    def can_see_evaluated_entity(evaluated_entity: EvaluatedEntity):
        # FIXME TODO
        return bool(evaluated_entity)

    def bounds(self):
        return self._bounds

    def clear_bounds(self):
        self._bounds = []
        return self

    def add_bound(self, component):
        self._bounds.append(component)
        return self

    def set_component(self, component: ComponentType):
        self._components[component.component_enum] = component
        return self

    def get_component(self, component: typing.Type[ComponentType]):
        return self._components.get(component.component_enum)

    def can_receive_messages(self) -> bool:
        assert not self.itsme, 'Requested if your own entity can receive messages.. well, it can.'
        from core.src.world.components.character import CharacterComponent
        v = self._components.get(CharacterComponent.component_enum, None)
        return bool(v and v.value)
