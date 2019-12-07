from functools import wraps


def singleton_action(fn):
    @wraps(fn)
    async def decorator(entity, *a, **kw):
        from core.src.world.builder import singleton_actions_scheduler
        await singleton_actions_scheduler.stop_current_action_if_exists(entity.entity_id)
        return await fn(entity, *a, **kw)
    return decorator
