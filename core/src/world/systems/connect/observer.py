import asyncio
import typing

from core.src.world.actions.cast import cast_entity
from core.src.world.actions.look import look
from core.src.world.builder import world_repository
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity, EntityID
from core.src.world.utils.entity_utils import get_base_room_for_entity
from core.src.world.utils.world_types import Transport


class ConnectionsObserver:
    def __init__(self, transport):
        self._commands = {}
        self.transport = transport

    def add_command(self, command: str, method: callable):
        self._commands[command] = method

    async def on_message(self, message: typing.Dict):
        assert message['c'] == 'connected'
        entity = Entity(EntityID(message['e_id']), transport=Transport(message['n'], self.transport))
        await self.on_connect(entity)

    async def on_connect(self, entity: Entity):
        pos = world_repository.get_component_value_by_entity(entity.entity_id, PosComponent)
        if not pos:
            await cast_entity(entity, get_base_room_for_entity(entity))
            await self.greet(entity)
        await look(entity)

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
