import datetime
import time
import hashlib
import hmac
import typing

import itertools
from redis import StrictRedis
from core.src.auth.logging_factory import LOGGER


WebsocketChannel = typing.NamedTuple(
    'WebsocketChannel',
    (
        ('entity_id', int),
        ('created_at', int),
        ('id', str)
    )
)


def _ws_channel_factory(a: typing.Tuple[bytes, bytes]) -> WebsocketChannel:
    k, v = a
    data = v.decode().split(',')
    assert len(data) == 2
    return WebsocketChannel(
        id=k.decode().replace('c:', ''),
        entity_id=int(data[0]),
        created_at=int(data[1])
    )


class WebsocketChannelsRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self._prefix = 'wschans'

    def create(self, entity_id: int) -> WebsocketChannel:
        LOGGER.core.debug('WebsocketChannelsRespository.create(%s)', entity_id)
        key = hashlib.sha256(str(entity_id).encode()).digest()
        nonce = datetime.datetime.now().isoformat().encode()
        connection_id = hmac.HMAC(key, '{}:{}'.format(entity_id, nonce).encode(), digestmod=hashlib.sha256).hexdigest()
        now = int(time.time())
        self.redis.hset(self._prefix, 'c:' + connection_id, '{},{}'.format(entity_id, now))
        response = WebsocketChannel(entity_id=entity_id, id=connection_id, created_at=now)
        LOGGER.core.debug('WebsocketChannelsRespository.create(%s) response: %s', entity_id, response)
        return response

    def delete(self, connection_id: str):
        LOGGER.core.debug('WebsocketChannelsRespository.delete(%s)', connection_id)
        return self.redis.hdel(self._prefix, 'c:' + connection_id)

    def get(self, connection_id: str) -> typing.Optional[WebsocketChannel]:
        LOGGER.core.debug('WebsocketChannelsRespository.get(%s)', connection_id)
        res = self.redis.hget(self._prefix, 'c:' + connection_id)
        if not res:
            return
        data = res.decode().split(',')
        assert len(data) == 2, data
        response = WebsocketChannel(entity_id=data[0], id=connection_id, created_at=data[1])
        LOGGER.core.debug('WebsocketChannelsRespository.get(%s) response: %s', connection_id, response)
        return response

    def get_many(self, *connection_ids: str) -> typing.Dict:
        response = dict()
        res = self.redis.hmget(self._prefix, *('c:{}'.format(connection_id) for connection_id in connection_ids))
        for c_id, ch in zip(connection_ids, res):
            ch = ch and ch.decode().split(',')
            response[c_id] = ch and WebsocketChannel(entity_id=ch[0], id=c_id, created_at=ch[1])
        return response

    def get_active_channels(self) -> typing.Iterable[WebsocketChannel]:
        try:
            return map(_ws_channel_factory, self.redis.hscan_iter(self._prefix))
        except:
            raise
