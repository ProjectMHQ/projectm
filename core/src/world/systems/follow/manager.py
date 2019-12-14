import typing


class FollowSystemManager:
    def __init__(self):
        self._follows_by_target = {}
        self._follow_by_follower = {}

    def stop_following(self, follower_id: int):
        pass

    def follow(self, follower_id: int, target_id: int):
        pass

    def on_event(self, event: typing.Dict):
        pass
