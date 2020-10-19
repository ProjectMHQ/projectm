import asyncio

import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain import DomainObject
from core.src.world.domain.entity import Entity
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
            components_data = await world_repository.get_components_values_by_components(
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
    if isinstance(item, dict):
        payload = item  # fixme need client cooperation to fix this.
    else:
        item_type, details = serialize_system_message_item(item)
        payload = {
            "event": event_type,
            "target": item_type,
            "details": details
        }
    return await transport.send_system_event(entity.get_component(ConnectionComponent).value, payload)


async def emit_room_msg(origin: Entity, message_template, target: Entity = None, room=None):
    from core.src.world.builder import world_repository
    from core.src.world.builder import transport
    room = room or (origin.get_room() or await get_current_room(origin))
    elegible_listeners = await world_repository.get_elegible_listeners_for_room(room)
    elegible_listeners = [l for l in elegible_listeners if l not in (
        origin and origin.entity_id, target and target.entity_id
    )]
    components_data = await world_repository.get_components_values_by_components(
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
