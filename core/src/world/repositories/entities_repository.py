import time
import typing

from redis import StrictRedis

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
        return self.redis.eval(script, 0, now)

    def get_entity(self, entity_id: int, components: typing.Optional[typing.Tuple[BaseComponentType]]) -> typing.List:
        return self.redis.hmget('{}:{}'.format(self.prefix, entity_id), components)

    def update_entity_properties(self, entity_id: int, **components: typing.Dict[str, str]):
        return self.redis.hmget('{}:{}'.format(self.prefix, entity_id), components)
