from redis import StrictRedis

from core.src.logging_factory import LOGGER
from core.src.world.components.types import ComponentType
from core.src.world.types import Bit


class MapRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis

    def get_entity_position(self, entity_id: int):
        raise NotImplementedError
