import asyncio
import typing

from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.utils.utils import ActionTarget
from core.src.world.domain import DomainObject
from core.src.world.domain.entity import Entity
from core.src.world.utils.serialization import serialize_system_message_item


async def emit_msg(item, message: str):
    from core.src.world.builder import transport
    if isinstance(item, ActionTarget):
        namespace = item.components.connection.value
    elif isinstance(item, Entity):
        namespace = item.transport.namespace
    else:
        raise ValueError
    return await transport.send_message(namespace, message)


async def emit_system_message(entity, event_type: str, item: (DomainObject, typing.NamedTuple)):
    from core.src.world.builder import transport
    assert isinstance(item, (DomainObject, ActionTarget)), item
    item_type, details = serialize_system_message_item(item)
    payload = {
        "event": event_type,
        "target": item_type,
        "details": details
    }
    if isinstance(entity, ActionTarget):
        namespace = item.components.connection.value
    else:
        namespace = entity.transport.namespace
    return await transport.send_system_event(namespace, payload)


async def emit_room_msg(room, origin_attributes, action_target, message_template):
    from core.src.world.builder import world_repository
    from core.src.world.builder import transport
    elegible_listeners = await world_repository.get_elegible_listeners_for_room(room)
    components_data = await world_repository.get_components_values_by_components(
        elegible_listeners, [ConnectionComponent, PosComponent]
    )
    futures = []
    for entity_id, value in components_data[PosComponent.component_enum].items():
        if entity_id == action_target.entity_id:
            continue
        if value == room.position.value and components_data[ConnectionComponent.component_enum][entity_id]:
            # TODO - Evaluate VS entity memory
            msg_template_arguments = {
                'origin': origin_attributes.keyword,
                'target': action_target.components.target_attributes.keyword
            }
            futures.append(
                transport.send_message(
                    components_data[ConnectionComponent.component_enum][entity_id],
                    message_template.format(**msg_template_arguments)
                )
            )
    await asyncio.gather(*futures)
