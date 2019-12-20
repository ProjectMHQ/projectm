import asyncio
import typing

from core.src.world import exceptions
from core.src.world.actions.follow import do_follow
from core.src.world.utils.world_types import Transport

from core.src.world.entity import Entity, EntityID


class FollowSystemManager:
    def __init__(self, transports_manager, loop=asyncio.get_event_loop()):
        self.transports_manager = transports_manager
        self._follows_by_target: typing.Dict[int, typing.List] = {}
        self._follow_by_follower: typing.Dict[int, int] = {}
        self.loop = loop

    def stop_following(self, follower_id: int):
        followed_id = self._follow_by_follower.get(follower_id)
        if followed_id:
            self._follows_by_target[followed_id].remove(follower_id)
            followed = self._follow_by_follower.pop(follower_id)
            if not self._follows_by_target.get(followed_id):
                assert not self._follows_by_target.pop(followed_id)
            return followed

    def follow_entity(self, follower_id: int, target_id: int):
        self._follow_by_follower[follower_id] = target_id
        if not self._follows_by_target.get(target_id):
            self._follows_by_target[target_id] = [follower_id]
        else:
            self._follows_by_target[target_id].append(follower_id)

    def is_follow_repetition(self, follower, target) -> bool:
        return self._follow_by_follower.get(follower) == target

    def is_follow_loop(self, follower, target):
        follower_followers = self._follows_by_target.get(follower, [])
        if target in follower_followers:
            return True
        for f in follower_followers:
            if self.is_follow_loop(follower, f):
                return True

    async def on_event(self, event: typing.Dict):
        assert event['event'] == 'move'
        assert event['action'] == 'leave'
        followers_ids = self._follows_by_target.get(event['entity']['id'], [])
        followers_ids and await asyncio.gather(
            *(self._do_follow(f_id, event) for f_id in followers_ids)
        )

    async def _do_follow(self, follower_id: int, event: typing.Dict):
        current_followed_id = self._follow_by_follower.get(follower_id)
        if current_followed_id != event['entity']['id']:
            return
        transport: Transport = self.transports_manager.get_transport_by_entity_id(follower_id)
        entity = Entity(EntityID(follower_id), transport=transport)
        self.loop.create_task(do_follow(entity, event))

