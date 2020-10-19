import asyncio
import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.actions.movement.move import do_move_entity
from core.src.world.components.character import CharacterComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room
from core.src.world.utils.entity_utils import load_components


class FollowSystemManager:
    def __init__(self, transports_manager, loop=asyncio.get_event_loop()):
        self.transports_manager = transports_manager
        self._follows_by_target: typing.Dict[int, typing.List] = {}
        self._follow_by_follower: typing.Dict[int, int] = {}
        self.loop = loop

    def get_follow_target(self, follower_id: int):
        response = self._follow_by_follower.get(follower_id)
        return response and Entity(response).set_component(CharacterComponent(True))

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

    def is_following_someone(self, follower):
        return bool(self._follow_by_follower.get(follower))

    def is_followed(self, target):
        return bool(self._follows_by_target.get(target))

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
            LOGGER.core.error('Error on follow system')
            return
        entity = await load_components(Entity(follower_id), ConnectionComponent, PosComponent)
        if entity.get_component(PosComponent).value != event['from']:
            LOGGER.core.error('Error on follow system')
            return
        await do_move_entity(
            entity,
            Room(PosComponent(event['to'])),
            None,
            reason="movement",
            emit_message=False
        )
