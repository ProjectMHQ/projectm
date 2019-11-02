import typing

import time
from redis import StrictRedis
from core.src.world.repositories.abtracts import RedisRepositoryAbstract


class RedisCharacterRepositoryImpl(RedisRepositoryAbstract):
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'ch/'

    def exists(self, character_id: str):
        return bool(self.redis.exists(self.prefix + character_id))

    def create(self, character_id: str, name: str) -> typing.Dict:
        payload = {
            "name": name,
            "created_at": int(time.time()),
        }
        self.redis.hmset('ch/' + character_id, payload)
        return payload

    def get(self, character_id: str, *values) -> typing.Dict:
        data = self.redis.hmget(self.prefix + character_id, *values)
        return data

    def set(self, character_id: str, *values: typing.Tuple[str, typing.Any]):
        self.redis.hmset(self.prefix + character_id, **{a: b for a, b in values})
