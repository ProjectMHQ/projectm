from core.src.world.actions.movement.follow_messages import FollowMessages
from core.src.world.components.attributes import AttributesComponent
from core.src.world.utils.messaging import emit_msg, emit_room_msg
from core.src.world.actions_scheduler.tools import singleton_action
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import search_entity_by_keyword

messages = FollowMessages()


@singleton_action
async def follow(entity: Entity, *arguments: str):
    from core.src.world.builder import follow_system_manager
    assert len(arguments) == 1
    if not len(arguments):
        return await unfollow(entity)
    target_entity = await search_entity_by_keyword(entity, arguments[0])
    if not target_entity:
        await emit_msg(entity, messages.target_not_found())
    elif entity.entity_id == target_entity.entity_id:
        await unfollow(entity)
    else:
        if follow_system_manager.is_follow_repetition(entity.entity_id, target_entity.entity_id):
            await emit_msg(entity, messages.already_following_target())
        elif follow_system_manager.is_follow_loop(entity, target_entity):
            await emit_msg(entity, messages.follow_is_loop())
        if await emit_msg(
            target_entity,
            messages.follow_entity(entity.get_component(AttributesComponent))
        ):
            follow_system_manager.follow_entity(entity.entity_id, target_entity.entity_id)
            await emit_room_msg(
                origin=entity,
                target=target_entity,
                message_template=messages.entity_follows_entity_template()
            )


async def unfollow(entity):
    from core.src.world.builder import follow_system_manager
    target_entity = follow_system_manager.get_follow_target(entity.entity_id)
    if not target_entity:
        await emit_msg(entity, messages.not_following_anyone())
    follow_system_manager.stop_following(entity.entity_id)
    await emit_msg(entity, messages.do_unfollow(target_entity))
    await emit_msg(entity, messages.do_unfollow(target_entity))
    await emit_room_msg(
        origin=entity,
        target=target_entity,
        message_template=messages.entity_follows_entity_template()
    )
