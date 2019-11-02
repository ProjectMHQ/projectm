import typing

from redis import StrictRedis
from core.src.world.components import ComponentTypeEnum


class ComponentsRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.entities_prefix = 'e'

    def get_components_values(self, entity_id: str, *component_key: ComponentTypeEnum) -> \
            typing.Iterable[typing.Optional[bytes]]:
        return self.redis.hmget('{}:{}'.format(self.entities_prefix, entity_id), *component_key)
