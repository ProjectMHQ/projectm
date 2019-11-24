import asyncio
from asyncio import coroutine


class SingletonActionsScheduler:
    def __init__(self, loop=asyncio.get_event_loop()):
        self.loop = loop
        self.schedule = {}

    async def schedule(self, entity_id: int, action: coroutine):
        curr_action = self.schedule.get(entity_id)
        if not curr_action:
            await self._schedule_action(entity_id, action)
        if curr_action.can_be_stopped_by(action):
            await curr_action.stop()
            await self._schedule_action(entity_id, action)

    async def _schedule_action(self, entity_id: int, action: coroutine):
        self.schedule[entity_id] = action
        self.loop.create_task(action.scheduled())
