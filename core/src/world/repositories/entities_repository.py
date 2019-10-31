import time
import typing

from redis import StrictRedis

from core.src.logging_factory import LOGGING_FACTORY
from core.src.world.domain.components import Components
from core.src.world.domain.components.types import BaseComponentType


class EntitiesRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'e'
        self.pipeline = None

    def create_entity(self):
        now = int(time.time())
        script = """
            local val=redis.call('bitpos', 'e:idmap', 0)
            redis.call('setbit', 'e:idmap', val, 1)
            local key = string.format('e:%s', val)
            redis.call('hmset', key, '{}', ARGV[1])
            return val
            """.format(Components.base.CREATED_AT.value)
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
