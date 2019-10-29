import typing
import uuid

from redis import StrictRedis
from core.src.websocket.types import WebsocketChannel


class WebsocketChannelsFactory:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self._prefix = 'ch/'

    def create(self, entity_id: str) -> WebsocketChannel:
        connection_id = str(uuid.uuid4())
        self.redis.hmset(
            'e/' + entity_id, {"connection_id": connection_id}
        )
        self.redis.set(self._prefix + 'e/' + entity_id, connection_id)
        self.redis.set(self._prefix + 'c/' + connection_id, entity_id)
        return WebsocketChannel(entity_id=entity_id, channel_id=channel_id)

    def delete(self, entity_id: str=None, channel_id: str=None) -> bool:
        if not entity_id and not channel_id:
            raise ValueError('Error, at least one must be declared (both is better)')
        channel_id = channel_id or self.redis.get(self._prefix + 'e/' + entity_id)
        entity_id = entity_id or self.redis.get(self._prefix + 'c/' + channel_id)
        self.redis.delete(self._prefix + 'e/' + entity_id, self._prefix + 'c/' + channel_id)
        return True

    def get_from_entity_id(self, entity_id: str) -> typing.Optional[WebsocketChannel]:
        res = self.redis.get(self._prefix + 'e/' + entity_id)
        if not res:
            return
        return WebsocketChannel(entity_id=entity_id, channel_id=res.decode())

    def get_from_channel(self, channel_id: str) -> typing.Optional[WebsocketChannel]:
        res = self.redis.get(self._prefix + 'c/' + channel_id)
        if not res:
            return
        return WebsocketChannel(entity_id=res and res.decode(), channel_id=channel_id)

    def get_active_channels(self):
        keys = self.redis.keys(self._prefix + 'c/*')
        return (
            WebsocketChannel(channel_id=c, entity_id=e) for c, e in
            {
                keys[i].decode().replace(self._prefix + 'c/', ''): v.decode()
                for i, v in enumerate(self.redis.mget(list(keys)))
            }.items()
        )
