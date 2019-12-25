from asyncio import coroutine
from functools import wraps

from core.src.world.actions_scheduler.looped_scheduled_actions_factories import LoopedScheduledAction
from core.src.world.actions_scheduler.scheduled_actions_factories import ScheduledAction, ActionType
from core.src.world.entity import Entity


def singleton_action(fn):
    @wraps(fn)
    async def decorator(entity, *a, **kw):
        from core.src.world.builder import singleton_actions_scheduler
        await singleton_actions_scheduler.stop_current_action_if_exists(entity.entity_id)
        return await fn(entity, *a, **kw)
    return decorator


def cancellable_scheduled_action_factory(entity: Entity, action: coroutine, wait_for=0):
    return ScheduledAction(
        entity,
        action,
        ActionType.CANCELLABLE,
        wait_for
    )


def looped_cancellable_scheduled_action_factory(entity: Entity, action: coroutine, wait_for=0):
    return LoopedScheduledAction(
        entity,
        action,
        ActionType.CANCELLABLE,
        wait_for
    )
