import typing
from redis import StrictRedis
from core.src.logging_factory import LOGGER
from core.src.world.components.types import ComponentType
from core.src.world.entity import Entity


class EntitiesRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'e'
        self.pipeline = None
        self.bitmap_key = self.prefix + ':idmap'
        redis.setbit(self.bitmap_key, 0, 1)  # ensure the map is 1 based

    def _allocate_entity_id(self) -> int:
        script = """
            local val=redis.call('bitpos', '{0}', 0)
            redis.call('setbit', '{0}', val, 1)
            local key = string.format('{1}:%s', val)
            redis.call('hmset', key, 'entity', 1)
            return val
            """\
            .format(self.bitmap_key, self.prefix)
        response = self.redis.eval(script, 0)
        LOGGER.core.debug('EntityRepository.create_entity, response: %s', response)
        assert response
        return int(response)

    def save_entity(self, entity: Entity):
        assert not entity.entity_id, 'entity_id: %s, use update, not save.' % entity.entity_id
        entity_id = self._allocate_entity_id()
        entity.entity_id = entity_id
        self.update_entity(entity)

    def get_entity(
            self,
            entity_id: int,
            components: typing.Optional[typing.Tuple[ComponentType]]
    ) -> typing.Optional[typing.List]:
        response = self.redis.hmget('{}:{}'.format(self.prefix, entity_id), components)
        LOGGER.core.debug('EntityRepository.get_entity(%s, %s), response: %s', entity_id, components, response)
        return response

    def update_entity(self, entity: Entity):
        assert entity.entity_id
        entity_updates = {c.key: c.value for c in entity.pending_changes.items()}
        response = self.redis.hmset(entity.entity_id, entity_updates)
        entity.pending_changes.clear()
        LOGGER.core.debug(
            'EntityRepository.update_entity_components(%s, %s), response: %s',
            entity.entity_id, entity_updates, response
        )
        return response
