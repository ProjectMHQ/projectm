import asyncio
import typing

from core.src.world.actions.cast import cast_entity
from core.src.world.actions.getmap import getmap
from core.src.world.actions.look import look
from core.src.world.builder import world_repository, events_subscriber_service, pubsub_observer
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity, EntityID
from core.src.world.utils.entity_utils import get_base_room_for_entity
from core.src.world.utils.world_types import Transport


class ConnectionsObserver:
    def __init__(self, transport, loop=asyncio.get_event_loop()):
        self._commands = {}
        self.transport = transport
        self.loop = loop

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

    @staticmethod
    async def on_disconnect(entity: Entity):
        current_connection = list(world_repository.get_raw_component_value_by_entity_ids(
            ConnectionComponent, entity.entity_id
        ))[0]
        if current_connection == entity.transport.namespace:
            world_repository.update_entities(entity.set(ConnectionComponent("")))
            events_subscriber_service.remove_observer_for_entity_id(entity.entity_id)
            await events_subscriber_service.unsubscribe_all(entity)

    async def on_connect(self, entity: Entity):
        world_repository.update_entities(
            entity.set(ConnectionComponent(entity.transport.namespace))
        )
        events_subscriber_service.add_observer_for_entity_id(entity.entity_id, pubsub_observer)
        pos = world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        if not pos:
            await cast_entity(entity, get_base_room_for_entity(entity))
            self.loop.create_task(self.greet(entity))
        else:
            await cast_entity(entity, get_base_room_for_entity(entity), update=False)
        self.loop.create_task(asyncio.gather(look(entity), getmap(entity)))

    async def greet(self, entity: Entity):
        await entity.emit_msg(  # FIXME TEST - Remove
            {
                "event": "greet",
                "message": "Welcome to a new place!"
            }
        )
        await asyncio.sleep(3)
        await entity.emit_msg(
            {
                "event": "greet",
                "message": "Look around..."
            }
        )
        await asyncio.sleep(3)
        await entity.emit_msg(
            {
                "event": "greet",
                "message": "...but be careful!"
            }
        )
