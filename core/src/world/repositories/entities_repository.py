import time
import typing

from redis import StrictRedis

from core.src.logging_factory import LOGGING_FACTORY
from core.src.world.components import Components
from core.src.world.components.types import BaseComponentType


class EntitiesRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'e'
        self.pipeline = None
        self.bitmap_key = self.prefix + ':idmap'
        assert self.redis.getbit(self.bitmap_key, 0)

    def create_entity(self):
        now = int(time.time())
        script = """
            local val=redis.call('bitpos', '{0}', 0)
            redis.call('setbit', '{0}', val, 1)
            local key = string.format('{1}:%s', val)
            redis.call('hmset', key, '{2}', ARGV[1])
            return val
            """.format(
            self.bitmap_key,
            self.prefix,
            Components.base.CREATED_AT.value
        )
        response = self.redis.eval(script, 0, now)
        LOGGING_FACTORY.core.debug('EntityRepository.create_entity, response: %s', response)
        return response and int(response)

    def get_entity(
            self,
            entity_id: int,
            components: typing.Optional[typing.Tuple[BaseComponentType]]
    ) -> typing.Optional[typing.List]:
        response = self.redis.hmget('{}:{}'.format(self.prefix, entity_id), components)
        LOGGING_FACTORY.core.debug('EntityRepository.get_entity(%s, %s), response: %s', entity_id, components, response)
        return response

    def update_entity_properties(self, entity_id: int, **components: typing.Dict[str, str]):
        response = self.redis.hmget('{}:{}'.format(self.prefix, entity_id), components)
        LOGGING_FACTORY.core.debug(
            'EntityRepository.update_entity_properties(%s, %s), response: %s', entity_id, components, response
        )
        return response
