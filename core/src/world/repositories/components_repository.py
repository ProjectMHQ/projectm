from redis import StrictRedis

from core.src.world.domain.components.types import ComponentType
from core.src.world.types import Bit


class ComponentsRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis

    def activate_component_for_entity(self, component_type: ComponentType, entity_id: str) -> Bit:
        self.redis.setbit(component_type.name, entity_id, Bit.ON)
        return Bit.ON

    def deactivate_component_for_entity(self, component_type: ComponentType, entity_id: str) -> Bit:
        self.redis.setbit(component_type.name, entity_id, Bit.OFF)
        return Bit.OFF
