import datetime
import time
import hashlib
import hmac
import typing
from redis import StrictRedis
from core.src.logging_factory import LOGGING_FACTORY


WebsocketChannel = typing.NamedTuple(
    'WebsocketChannel',
    (
        ('entity_id', int),
        ('connection_id', str),
        ('created_at', int)
    )
)


class WebsocketChannelsRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self._prefix = 'wschans'

    def create(self, entity_id: int) -> WebsocketChannel:
        LOGGING_FACTORY.core.debug('WebsocketChannelsRespository.create(%s)', entity_id)
        key = hashlib.sha256(str(entity_id).encode()).digest()
        nonce = datetime.datetime.now().isoformat().encode()
        connection_id = hmac.HMAC(key, '{}:{}'.format(entity_id, nonce).encode(), digestmod=hashlib.sha256).hexdigest()
        now = int(time.time())
        self.redis.hset(self._prefix, 'c:' + connection_id, '{},{}'.format(entity_id, now))
        response = WebsocketChannel(entity_id=entity_id, connection_id=connection_id, created_at=now)
        LOGGING_FACTORY.core.debug('WebsocketChannelsRespository.create(%s) response: %s', entity_id, response)
        return response

    def delete(self, connection_id: str):
        LOGGING_FACTORY.core.debug('WebsocketChannelsRespository.delete(%s)', connection_id)
        return self.redis.hdel(self._prefix, 'c:' + connection_id)

    def get(self, connection_id: str) -> typing.Optional[WebsocketChannel]:
        LOGGING_FACTORY.core.debug('WebsocketChannelsRespository.get(%s)', connection_id)
        res = self.redis.hget(self._prefix, 'c:' + connection_id)
        if not res:
            return
        data = res.decode().split(',')
        assert len(data) == 2, data
        response = WebsocketChannel(entity_id=data[0], connection_id=connection_id, created_at=data[1])
        LOGGING_FACTORY.core.debug('WebsocketChannelsRespository.get(%s) response: %s', connection_id, response)
        return response

    def get_active_channels(self) -> typing.Iterable[WebsocketChannel]:
        def _ws(k: bytes, v: bytes) -> WebsocketChannel:
            data = v.decode().split(',')
            assert len(data) == 2
            return WebsocketChannel(
                connection_id=k.decode().replace('c:', ''),
                entity_id=int(data[0]),
                created_at=int(data[1])
            )
        return map(_ws, self.redis.hscan(self._prefix)[1].items())