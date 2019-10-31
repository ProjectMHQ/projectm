from redis import StrictRedis

from core.src.logging_factory import LOGGING_FACTORY
from core.src.world.domain.components.types import ComponentType
from core.src.world.types import Bit


class ComponentsRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis

    def activate_component_for_entity(self, component_type: ComponentType, entity_id: int) -> Bit:
        LOGGING_FACTORY.core.debug('Component %s, Entity %s, Bit ON', component_type.value, entity_id)
        self.redis.setbit(component_type.value, int(entity_id), Bit.ON)
        return Bit.ON

    def deactivate_component_for_entity(self, component_type: ComponentType, entity_id: int) -> Bit:
        LOGGING_FACTORY.core.debug('Component %s, Entity %s, Bit OFF', component_type.value, entity_id)
        self.redis.setbit(component_type.value, int(entity_id), Bit.OFF)
        return Bit.OFF
