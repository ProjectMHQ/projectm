import asyncio

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain import DomainObject
from core.src.world.domain.entity import Entity
from core.src.world.utils.serialization import serialize_system_message_item


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
            assert connection_id
            entity.set_component(ConnectionComponent(connection_id))
            await transport.send_message(
                entity.get_component(ConnectionComponent).value,
                message
            )
    return True


async def emit_sys_msg(entity, event_type: str, item: (DomainObject, Entity)):
    from core.src.world.builder import transport
    item_type, details = serialize_system_message_item(item)
    payload = {
        "event": event_type,
        "target": item_type,
        "details": details
    }
    return await transport.send_system_event(entity.get_component(ConnectionComponent).value, payload)


async def emit_room_msg(origin: Entity, message_template, target: Entity = None):
    from core.src.world.builder import world_repository
    from core.src.world.builder import transport
    room = origin.get_room()
    elegible_listeners = await world_repository.get_elegible_listeners_for_room(room)
    elegible_listeners = [l for l in elegible_listeners if l not in (origin.entity_id, target.entity_id)]
    components_data = await world_repository.get_components_values_by_components(
        elegible_listeners, [ConnectionComponent, PosComponent]
    )
    futures = []
    for entity_id, value in components_data[PosComponent.component_enum].items():
        if value == room.position.value and components_data[ConnectionComponent.component_enum][entity_id]:
            # TODO - Evaluate VS entity memory
            msg_template_arguments = {
                'origin': origin.get_component(AttributesComponent).keyword,
                'target': target and target.get_component(AttributesComponent).keyword
            }
            futures.append(
                transport.send_message(
                    components_data[ConnectionComponent.component_enum][entity_id],
                    message_template.format(**msg_template_arguments)
                )
            )
    await asyncio.gather(*futures)
