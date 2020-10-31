import asyncio
import typing

from core.src.world.actions.system.cast import cast_entity
from core.src.world.actions.system.disconnect import disconnect_entity
from core.src.world.actions.system.getmap import getmap
from core.src.world.actions.look.look import look
from core.src.world.components.pos import PosComponent
from core.src.world.components.system import SystemComponent

from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import get_base_room_for_entity, update_entities
from core.src.world.utils.messaging import emit_msg


class ConnectionsObserver:
    def __init__(
            self,
            transport,
            pubsub_observer,
            world_repository,
            events_subscriber_service,
            connections_manager,
            commands_observer,
            loop=asyncio.get_event_loop()
    ):
        self._commands = {}
        self.transport = transport
        self.loop = loop
        self.pubsub_observer = pubsub_observer
        self.world_repository = world_repository
        self.events_subscriber_service = events_subscriber_service
        self.manager = connections_manager
        self.commands_observer = commands_observer

    def add_command(self, command: str, method: callable):
        self._commands[command] = method

    async def on_message(self, message: typing.Dict):
        entity = Entity(
            message['e_id'], itsme=True
        ).set_component(SystemComponent().connection.set(message['n']))
        if message['c'] == 'connected':
            await self.on_connect(entity)
        elif message['c'] == 'disconnected':
            await self.on_disconnect(entity)
        else:
            raise ValueError('wtf?!')

    async def on_disconnect(self, entity: Entity):
        current_connection = (await self.world_repository.read_struct_components_for_entity(
            entity.entity_id, (SystemComponent, 'connection')
        ))[SystemComponent.enum]
        if current_connection.connection.value != entity.get_component(SystemComponent).connection.value:
            return
        await disconnect_entity(entity, msg=False)
        self.events_subscriber_service.remove_observer_for_entity_id(entity.entity_id)
        self.manager.remove_transport(entity.entity_id)
        await self.events_subscriber_service.unsubscribe_all(entity)

    async def on_connect(self, entity: Entity):
        connection_id = entity.get_component(SystemComponent).connection.value
        self.events_subscriber_service.add_observer_for_entity_id(entity.entity_id, self.pubsub_observer)
        await update_entities(
            entity.set_for_update(SystemComponent().connection.set(connection_id))
        )
        pos = await self.world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        if not pos:
            await cast_entity(entity, get_base_room_for_entity(entity), on_connect=True, reason="connect")
            self.loop.create_task(self.greet(entity))
        else:
            await cast_entity(entity, pos, update=False, on_connect=True, reason="connect")
        self.manager.set_transport(entity.entity_id, connection_id)
        self.commands_observer.enable_channel(connection_id)
        self.loop.create_task(look(entity))
        self.loop.create_task(getmap(entity))

    async def greet(self, entity: Entity):
        await emit_msg(
            entity,
            "Welcome to a new place..."
        )
        await asyncio.sleep(3)
        await emit_msg(
            entity,
            "Look around..."
        )
        await asyncio.sleep(3)
        await emit_msg(
            entity,
            "..but be careful... "
        )
        await asyncio.sleep(3)
        await emit_msg(
            entity,
            "..Antani is on fire."
        )
