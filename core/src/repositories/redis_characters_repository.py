import typing

from redis import StrictRedis

from core.src.logging_factory import LOGGER


class RedisCharactersRepositoryImpl:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'char:e'

    def get_entity_id(self, character_id: str) -> typing.Optional[int]:
        response = self.redis.hget(self.prefix, character_id)
        LOGGER.core.debug('Character To Entity. character_id: %s, entity_id: %s', character_id, response)
        return response is not None and int(response)

    def set_entity_id(self, character_id: str, entity_id: str):
        assert not self.redis.hget(
            self.prefix, character_id
        ), 'character_id: %s, entity_id: %s' % (character_id, entity_id)

        response = self.redis.hset(self.prefix, character_id, entity_id)
        LOGGER.core.debug('Character To Entity. character_id: %s, entity_id: %s', character_id, response)
        return response
