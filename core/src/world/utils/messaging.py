import asyncio

import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.character import CharacterComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain import DomainObject
from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room
from core.src.world.utils.serialization import serialize_system_message_item
from core.src.world.utils.world_utils import get_current_room


async def emit_msg(entity, message: str):
    from core.src.world.builder import transport
    from core.src.world.builder import world_repository
    if entity.itsme:
        connection_id = entity.get_component(ConnectionComponent).value
        assert connection_id
        await transport.send_message(connection_id, message)
        return True
    else:
        assert entity.can_receive_messages()
        if not entity.get_component(ConnectionComponent):
            components_data = await world_repository.get_components_values_by_components_storage(
                [entity.entity_id], [ConnectionComponent]
            )
            connection_id = components_data[ConnectionComponent.component_enum][entity.entity_id]
            if connection_id:
                entity.set_component(ConnectionComponent(connection_id))
                await transport.send_message(
                    entity.get_component(ConnectionComponent).value,
                    message
                )
                return True
    return False


async def emit_sys_msg(entity, event_type: str, item: (DomainObject, Entity, typing.Dict)):
    from core.src.world.builder import transport
    if event_type == 'map':  # fixme need client cooperation to fix this.
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
    return await transport.send_system_event(entity.get_component(ConnectionComponent).value, payload)


async def emit_room_sys_msg(entity: Entity, event_type: str, details: typing.Dict, room=None, include_origin=True):
    from core.src.world.builder import world_repository
    from core.src.world.builder import transport
    assert isinstance(details, dict)
    room = room or (entity.get_room() or await get_current_room(entity))
    elegible_listeners = await get_eligible_listeners_for_room(room)
    if not include_origin:
        elegible_listeners.remove(entity.entity_id)
    components_data = await world_repository.get_components_values_by_components_storage(
        elegible_listeners, [ConnectionComponent, PosComponent]
    )
    futures = []
    for entity_id, value in components_data[PosComponent.component_enum].items():
        if value == room.position.value and \
                components_data.get(ConnectionComponent.component_enum, {}).get(entity_id):
            payload = {
                "event": event_type,
                "target": "entity",
                "details": details,
                "position": room.position.value
            }
            futures.append(
                transport.send_system_event(
                    components_data[ConnectionComponent.component_enum][entity_id],
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
    from core.src.world.builder import world_repository
    from core.src.world.builder import transport
    room = room or (origin.get_room() or await get_current_room(origin))
    elegible_listeners = await get_eligible_listeners_for_room(room)
    elegible_listeners = [l for l in elegible_listeners if l not in (
        origin and origin.entity_id, target and target.entity_id
    )]
    components_data = await world_repository.get_components_values_by_components_storage(
        elegible_listeners, [ConnectionComponent, PosComponent]
    )
    futures = []
    for entity_id, value in components_data[PosComponent.component_enum].items():
        if value == room.position.value and components_data[ConnectionComponent.component_enum][entity_id]:
            # TODO - Evaluate VS entity memory
            futures.append(
                transport.send_message(
                    components_data[ConnectionComponent.component_enum][entity_id],
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


async def get_eligible_listeners_for_area(area: (PosComponent, Area)) -> typing.List[int]:
    """
    Returns the list of entities ids that are ables to receive messages in the selected area.
    The "area" argument is a PosComponent or an Area Object.
    If a PosComponent is passed, it is used as the Area center.
    """
    if isinstance(area, PosComponent):
        area = Area(area)
    from core.src.world.builder import map_repository
    from core.src.world.builder import world_repository
    entities_rooms = await map_repository.get_all_entity_ids_in_area(area)
    characters = entities_rooms and await world_repository.filter_entities_with_active_component(
        CharacterComponent, *entities_rooms
    )
    return characters


async def get_eligible_listeners_for_room(pos: (Room, PosComponent)) -> typing.List[int]:
    """
    Returns the list of entities ids that are ables to receive messages in the selected room.
    The "room" argument is a PosComponent or a Room Object.
    """
    if isinstance(pos, Room):
        pos = pos.position
    from core.src.world.builder import map_repository
    entities_room = await map_repository.get_room_content(pos)
    from core.src.world.builder import world_repository
    characters = entities_room and await world_repository.filter_entities_with_active_component(
        CharacterComponent, *entities_room
    ) or []
    return characters


def get_events_publisher():
    """
    Returns the intra-workers messaging events publisher.
    """
    from core.src.world.builder import events_publisher_service
    return events_publisher_service
