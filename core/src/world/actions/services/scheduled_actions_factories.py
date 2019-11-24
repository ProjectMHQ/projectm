import asyncio
from asyncio import coroutine
from enum import Enum

import time

from core.src.world.entity import Entity


def cancellable_scheduled_action_factory(entity: Entity, action: coroutine, wait_for=0):
    return ScheduledAction(
        entity,
        action,
        ActionType.CANCELLABLE,
        wait_for
    )


class ActionType(Enum):
    CANCELLABLE = 1
    BLOCKING = 2


class ScheduledAction:
    def __init__(self, entity, action, action_type, wait_for: int):
        self.action = action
        self.action_type = action_type
        self.entity = entity
        self.wait_for = wait_for
        self.must_be_stopped = False
        self.stopped = False
        self.done = False

    def can_be_stopped_by(self, other_action: 'ScheduledAction'):
        raise NotImplementedError

    def can_be_stopped(self):
        return bool(self.action_type == ActionType.CANCELLABLE)

    def stop(self):
        self.must_be_stopped = True

    async def blocking_stop(self, timeout=10):
        self.must_be_stopped = True
        timeout = int(time.time()) + timeout
        while int(time.time()) < timeout:
            await asyncio.sleep(0.01)
            if self.stopped:
                break
        if not self.stopped:
            raise ValueError('blocking_stop not working')  # TODO FIXME
        return True

    async def start(self, scheduler):
        run_at = int(time.time()) + self.wait_for
        while int(time.time()) < run_at:
            await asyncio.sleep(0.01)
            if self.must_be_stopped:
                break

        if self.must_be_stopped:
            await self.action.stop()
            self.stopped = True
        else:
            await self.action.do()
            self.stopped = True
            self.done = True
        scheduler.remove_action_for_entity_id(self.entity.entity_id)


