import typing
import uuid

from redis import StrictRedis
from core.src.websocket.types import WebsocketChannel


class WebsocketChannelsFactory:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self._prefix = 'ch/'

    def create(self, entity_id: str) -> WebsocketChannel:
        channel_id = str(uuid.uuid4())
        data = {
            'e/' + entity_id: channel_id,
            'c/' + channel_id: entity_id
        }
        self.redis.hmset(self._prefix, data)
        return WebsocketChannel(entity_id=entity_id, channel_id=channel_id)

    def delete(self, entity_id: str=None, channel_id: str=None) -> bool:
        if not entity_id and not channel_id:
            raise ValueError('Error, at least one must be declared (both is better)')
        channel_id = channel_id or self.redis.hmget(self._prefix, 'e/' + entity_id)
        entity_id = entity_id or self.redis.hmget(self._prefix, 'c/' + channel_id)
        self.redis.hdel(self._prefix, 'c/' + channel_id, 'e/' + entity_id)
        return True

    def get_from_entity_id(self, entity_id: str) -> typing.Optional[WebsocketChannel]:
        res = self.redis.hmget(self._prefix, 'e/' + entity_id)
        if not res[0]:
            return
        return WebsocketChannel(entity_id=entity_id, channel_id=res[0].decode())

    def get_from_channel(self, channel_id: str) -> typing.Optional[WebsocketChannel]:
        res = self.redis.hmget(self._prefix, 'c/' + channel_id)
        if not res[0]:
            return
        return WebsocketChannel(entity_id=res and res[0].decode(), channel_id=channel_id)
