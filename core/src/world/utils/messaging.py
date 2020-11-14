import asyncio

import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.position import PositionComponent
from core.src.world.components.system import SystemComponent
from core.src.world.domain import DomainObject
from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room
from core.src.world.utils.entity_utils import load_components, batch_load_components
from core.src.world.utils.serialization import serialize_system_message_item
from core.src.world.utils.world_utils import get_current_room


async def check_entity_can_receive_messages(entity):
    system_component = entity.get_component(SystemComponent)
    if not system_component:
        await load_components(entity, (SystemComponent, 'receive_events'))
    system_component = entity.get_component(SystemComponent)
    return system_component.receive_events


async def emit_msg(entity, message: str):
    from core.src.world.builder import transport
    from core.src.world.builder import world_repository
    if entity.itsme:
        connection_id = entity.get_component(SystemComponent).connection.value
        assert connection_id
        await transport.send_message(connection_id, message)
        return True
    else:
        if not entity.get_component(SystemComponent) or not entity.get_component(SystemComponent).connection:
            components_data = await world_repository.read_struct_components_for_entity(
                entity.entity_id, (SystemComponent, 'connection')
            )
            connection_id = components_data[SystemComponent.enum].connection.value
            if connection_id:
                entity.set_component(SystemComponent().connection.set(connection_id))
                await transport.send_message(
                    entity.get_component(SystemComponent).connection,
                    message
                )
                return True
    return False


async def emit_sys_msg(entity, event_type: (None, str), item: (DomainObject, Entity, typing.Dict)):
    from core.src.world.builder import transport
    if event_type in ('map', None):  # fixme need client cooperation to fix this.
        payload = item
    elif isinstance(item, dict):
        payload = {
            "event": event_type,
            "target": "entity",
            "details": item
        }
    else:
        item_type, details = serialize_system_message_item(item, entity)
        payload = {
            "event": event_type,
            "target": item_type,
            "details": details
        }
    return await transport.send_system_event(
        entity.get_component(SystemComponent).connection.value,
        payload
    )


async def emit_room_sys_msg(entity: Entity, event_type: str, details: typing.Dict, room=None, include_origin=True):
    from core.src.world.builder import transport
    assert isinstance(details, dict)
    room = room or (entity.get_room() or await get_current_room(entity))
    listeners = await get_eligible_listeners_for_room(room)
    if listeners:
        listeners = listeners if not include_origin else [e for e in listeners if e.entity_id != entity.entity_id]
        listeners and (
            await batch_load_components((SystemComponent, 'connection'), PositionComponent, entities=listeners)
        )
    futures = []
    for entity in listeners:
        position = entity.get_component(PositionComponent)
        if position.coord == room.position.coord and entity.get_component(SystemComponent).connection:
            payload = {
                "event": event_type,
                "target": "entity",
                "details": details,
                "position": room.position.value
            }
            futures.append(
                transport.send_system_event(
                    entity.get_component(SystemComponent).connection.value,
                    payload
                )
            )
    await asyncio.gather(*futures)


async def emit_room_msg(origin: Entity, message_template, target: Entity = None, room=None):
    """
    Emit a room message in the same room of "origin".
    The room can be overridden with the room= keyword argument, accepting a Room type as input.
    The message template must have a mandatory {origin} and an optional {target} placeholders.
    origin and target parameters must be type Entity, with the AttributesComponent loaded.
    origin is mandatory, target is optional.

    The emitted message type is a string, the target is the client text field.
    """
    from core.src.world.builder import transport
    room = room or (origin.get_room() or await get_current_room(origin))
    listeners = await get_eligible_listeners_for_room(room)
    listeners = [
        listener for listener in listeners if listener.entity_id not in (
            origin and origin.entity_id, target and target.entity_id
        )
    ]
    if not listeners:
        return
    await batch_load_components((SystemComponent, 'connection'), PositionComponent, entities=listeners)
    futures = []
    for entity in listeners:
        position = entity.get_component(PositionComponent)
        if position.coord == room.position.coord and entity.get_component(SystemComponent).connection:
            # TODO - Evaluate VS entity memory
            futures.append(
                transport.send_message(
                    entity.get_component(SystemComponent).connection.value,
                    message_template.format(
                        origin=origin.get_component(AttributesComponent).keyword,
                        target=target and target.get_component(AttributesComponent).keyword
                    )
                )
            )
    await asyncio.gather(*futures)


def get_stacker():
    """
    Returns a futures Stacker Object.
    The stacker is useful to batch messages to be executed (or canceled) at the end of an interaction.
    Methods:
         .add(emitter, emitter, ...)
         .execute()
         .load()
    """
    class Stacker:
        def __init__(self):
            self._messages = []

        def add(self, *msgs: callable):
            self._messages.append(msgs)

        async def execute(self):
            for msgs in self._messages:
                await asyncio.gather(*msgs)
            return True

        def cancel(self):
            _ = [[m.cancel() for m in msgs] for msgs in self._messages]
            return True

    return Stacker()


async def get_eligible_listeners_for_area(area: (PositionComponent, Area)) -> typing.List[int]:
    """
    Returns the list of entities ids that are ables to receive messages in the selected area.
    The "area" argument is a PosComponent or an Area Object.
    If a PosComponent is passed, it is used as the Area center.
    """
    if isinstance(area, PositionComponent):
        area = Area(area)
    from core.src.world.builder import map_repository
    from core.src.world.builder import world_repository
    entities_rooms = await map_repository.get_all_entity_ids_in_area(area)
    if not entities_rooms:
        return []
    entities = await world_repository.read_struct_components_for_entities(
        entities_rooms, (SystemComponent, 'receive_events')
    )
    return [int(entity_id) for entity_id in entities if entities[entity_id][SystemComponent.enum].receive_events]


async def get_eligible_listeners_for_room(pos: (Room, PositionComponent)) -> typing.List[Entity]:
    """
    Returns the list of entities ids that are ables to receive messages in the selected room.
    The "room" argument is a PosComponent or a Room Object.
    """
    if isinstance(pos, Room):
        pos = pos.position
    from core.src.world.builder import map_repository
    entities_room = [Entity(e) for e in await map_repository.get_room_content(pos)]
    if not entities_room:
        return []
    await batch_load_components((SystemComponent, 'receive_events'), entities=entities_room)
    return [e for e in entities_room if e.get_component(SystemComponent).receive_events]


def get_events_publisher():
    """
    Returns the intra-workers messaging events publisher.
    """
    from core.src.world.builder import events_publisher_service
    return events_publisher_service
