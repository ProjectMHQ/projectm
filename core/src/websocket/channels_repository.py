import datetime
import time
import hashlib
import hmac
import typing
import binascii
from redis import StrictRedis
from core.src.websocket.types import WebsocketChannel


class WebsocketChannelsRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self._prefix = 'wschans'

    def create(self, entity_id: int) -> WebsocketChannel:
        key = hashlib.sha256(str(entity_id).encode()).digest()
        nonce = datetime.datetime.now().isoformat().encode()
        connection_id = hmac.HMAC(key, '{}:{}'.format(entity_id, nonce).encode(), digestmod=hashlib.sha256).hexdigest()
        now = int(time.time())
        self.redis.hset(self._prefix, 'c:' + connection_id, '{},{}'.format(entity_id, now))
        return WebsocketChannel(entity_id=entity_id, connection_id=connection_id, created_at=now)

    def delete(self, connection_id: str):
        return self.redis.hdel(self._prefix, 'c:' + connection_id)

    def get(self, connection_id: str) -> typing.Optional[WebsocketChannel]:
        res = self.redis.hget(self._prefix, 'c:' + connection_id)
        if not res:
            return
        data = res.decode().split(',')
        assert len(data) == 2
        return WebsocketChannel(entity_id=data[0], connection_id=connection_id, created_at=data[1])

    def get_active_channels(self) -> typing.Iterable:
        def _ws(k: bytes, v: bytes):
            data = v.decode().split(',')
            assert len(data) == 2
            WebsocketChannel(
                connection_id=k.decode().replace('c:', ''),
                entity_id=data[0],
                created_at=data[1]
            )
        return map(_ws, self.redis.hscan(self._prefix)[1].items())
