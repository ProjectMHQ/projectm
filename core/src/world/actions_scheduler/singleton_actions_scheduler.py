import asyncio

from core.src.world.actions_scheduler.scheduled_actions_factories import ScheduledAction


class SingletonActionsScheduler:
    def __init__(self, loop=asyncio.get_event_loop()):
        self.loop = loop
        self._scheduled_actions = {}

    async def schedule(self, action: ScheduledAction):
        curr_action = self._scheduled_actions.get(action.entity.entity_id)
        if not curr_action:
            await self._schedule_action(action)
            return
        if curr_action.can_be_stopped():
            curr_action.stop()
            await self._schedule_action(action)

    async def _schedule_action(self, action: ScheduledAction):
        self._scheduled_actions[action.entity.entity_id] = action
        self.loop.create_task(action.start(self))

    async def stop_current_action_if_exists(self, entity_id: int):
        curr_action = self._scheduled_actions.get(entity_id)
        if curr_action:
            if not curr_action.can_be_stopped():
                return False
            curr_action.stop()
            self._scheduled_actions.pop(entity_id, None)
        return True

    def remove_action_for_entity_id(self, entity_id: int):
        self._scheduled_actions.pop(entity_id, None)
