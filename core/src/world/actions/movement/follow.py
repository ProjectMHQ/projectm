import asyncio

from core.src.world.actions.movement.follow_messages import FollowMessages
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.utils.messaging import emit_msg, emit_room_msg
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import search_entity_by_keyword, ensure_same_position, batch_load_components

messages = FollowMessages()


async def follow(entity: Entity, *arguments: str):
    from core.src.world.builder import follow_system_manager
    if not len(arguments):
        return await unfollow(entity)
    assert len(arguments) == 1
    target_entity = await search_entity_by_keyword(entity, arguments[0])
    if not target_entity:
        await emit_msg(entity, messages.target_not_found())
    elif entity.entity_id == target_entity.entity_id:
        if follow_system_manager.is_following_someone(entity.entity_id):
            await unfollow(entity)
        else:
            await emit_msg(entity, messages.not_following_anyone())
    else:
        if follow_system_manager.is_follow_repetition(entity.entity_id, target_entity.entity_id):
            await emit_msg(entity, messages.already_following_that_target())
        elif follow_system_manager.is_follow_loop(entity, target_entity):
            await emit_msg(entity, messages.follow_is_loop())
        else:
            if not await ensure_same_position(entity, target_entity):
                await emit_msg(entity, messages.target_not_found())
            previous_target = follow_system_manager.get_follow_target(entity.entity_id)
            if previous_target:
                await emit_msg(previous_target, messages.entity_stop_following_you(
                    entity.get_component(AttributesComponent).keyword
                ))
                follow_system_manager.stop_following(entity.entity_id)
            follow_system_manager.follow_entity(entity.entity_id, target_entity.entity_id)
            await asyncio.gather(
                emit_msg(entity, messages.follow_entity(target_entity.get_component(AttributesComponent).keyword)),
                emit_msg(
                    target_entity, messages.entity_is_following_you(entity.get_component(AttributesComponent).keyword)
                )
            )
            await emit_room_msg(
                origin=entity,
                target=target_entity,
                message_template=messages.entity_follows_entity_template(),
            )


async def unfollow(entity):
    from core.src.world.builder import follow_system_manager
    target_entity = follow_system_manager.get_follow_target(entity.entity_id)
    if not target_entity:
        await emit_msg(entity, messages.not_following_anyone())
    follow_system_manager.stop_following(entity.entity_id)
    await batch_load_components(
        AttributesComponent, ConnectionComponent, PosComponent,
        entities=(target_entity, entity)
    )
    await asyncio.gather(
        emit_msg(
            target_entity,
            messages.entity_stop_following_you(entity.get_component(AttributesComponent).keyword)
        ),
        emit_msg(entity, messages.do_unfollow(target_entity.get_component(AttributesComponent).keyword)),
        emit_room_msg(
            origin=entity,
            target=target_entity,
            message_template=messages.entity_follows_entity_template()
        )
    )
