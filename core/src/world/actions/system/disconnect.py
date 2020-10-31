from core.src.world.actions_scheduler.tools import singleton_action
from core.src.world.components.pos import PosComponent
from core.src.world.components.system import SystemComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import update_entities, load_components
from core.src.world.utils.messaging import emit_sys_msg, get_eligible_listeners_for_area, get_events_publisher


@singleton_action
async def disconnect_entity(entity: Entity, msg=True):
    from core.src.world.builder import map_repository
    from core.src.world.builder import websocket_channels_service
    from core.src.world.builder import cmds_observer
    events_publisher = get_events_publisher()
    await load_components(entity, PosComponent)
    listeners = await get_eligible_listeners_for_area(entity.get_component(PosComponent))
    await events_publisher.on_entity_disappear_position(
        entity, entity.get_component(PosComponent), "disconnect", listeners
    )
    msg and await emit_sys_msg(entity, "event", {"event": "quit"})
    current_channel_id = entity.get_component(SystemComponent).connection.value
    entity.set_for_update(SystemComponent().connection.set(""))
    if await update_entities(entity):
        await map_repository.remove_entity_from_map(entity.entity_id, entity.get_component(PosComponent))
        await websocket_channels_service.close_namespace_for_entity_id(entity.entity_id)
        cmds_observer.close_channel(current_channel_id)
