import asyncio
import typing

from core.src.world.actions.cast import cast_entity
from core.src.world.actions.disconnect import disconnect_entity
from core.src.world.actions.getmap import getmap
from core.src.world.actions.look import look
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity, EntityID
from core.src.world.utils.entity_utils import get_base_room_for_entity
from core.src.world.utils.world_types import Transport


class ConnectionsObserver:
    def __init__(
            self,
            transport,
            pubsub_observer,
            world_repository,
            events_subscriber_service,
            connections_manager,
            loop=asyncio.get_event_loop()
    ):
        self._commands = {}
        self.transport = transport
        self.loop = loop
        self.pubsub_observer = pubsub_observer
        self.world_repository = world_repository
        self.events_subscriber_service = events_subscriber_service
        self.manager = connections_manager

    def add_command(self, command: str, method: callable):
        self._commands[command] = method

    async def on_message(self, message: typing.Dict):
        entity = Entity(EntityID(message['e_id']), transport=Transport(message['n'], self.transport))
        if message['c'] == 'connected':
            await self.on_connect(entity)
        elif message['c'] == 'disconnected':
            await self.on_disconnect(entity)
        else:
            raise ValueError('wtf?!')

    async def on_disconnect(self, entity: Entity):
        current_connection = list(await self.world_repository.get_raw_component_value_by_entity_ids(
            ConnectionComponent, entity.entity_id
        ))
        if current_connection and current_connection[0] != entity.transport.namespace:
            return
        await disconnect_entity(entity)
        self.events_subscriber_service.remove_observer_for_entity_id(entity.entity_id)
        self.manager.remove_transport(entity.entity_id)
        await self.events_subscriber_service.unsubscribe_all(entity)

    async def on_connect(self, entity: Entity):
        await self.world_repository.update_entities(
            entity.set(ConnectionComponent(entity.transport.namespace))
        )
        self.events_subscriber_service.add_observer_for_entity_id(entity.entity_id, self.pubsub_observer)
        pos = await self.world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        if not pos:
            await cast_entity(entity, get_base_room_for_entity(entity), on_connect=True, reason="connect")
            self.loop.create_task(self.greet(entity))
        else:
            await cast_entity(entity, pos, update=False, on_connect=True, reason="connect")
        self.manager.set_transport(entity.entity_id, entity.transport)
        self.loop.create_task(look(entity))
        self.loop.create_task(getmap(entity))

    async def greet(self, entity: Entity):
        await entity.emit_msg(
            "Welcome to a new place..."
        )
        await asyncio.sleep(3)
        await entity.emit_msg(
            "Look around..."
        )
        await asyncio.sleep(3)
        await entity.emit_msg(
            "..but be careful... "
        )
        await asyncio.sleep(3)
        await entity.emit_msg(
            "..Antani is on fire."
        )
