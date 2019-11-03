import typing

import os

import binascii

import bitarray
from redis import StrictRedis
from core.src.logging_factory import LOGGER
from core.src.world.components import ComponentType
from core.src.world.entity import Entity


class EntitiesRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self._entity_prefix = 'e'
        self._component_prefix = 'c'
        self._map_suffix = 'm'
        self._data_suffix = 'd'
        redis.setbit('{}:{}'.format(self._entity_prefix, self._map_suffix), 0, 1)  # ensure the map is 1 based

    def _allocate_entity_id(self) -> int:
        script = """
            local val = redis.call('bitpos', '{0}:{1}', 0)
            redis.call('setbit', '{0}:{1}', val, 1)
            return val
            """\
            .format(self._entity_prefix, self._map_suffix)
        response = self.redis.eval(script, 0)
        LOGGER.core.debug('EntityRepository.create_entity, response: %s', response)
        assert response
        return int(response)

    def save_entity(self, entity: Entity) -> Entity:
        assert not entity.entity_id, 'entity_id: %s, use update, not save.' % entity.entity_id
        entity_id = self._allocate_entity_id()
        entity.entity_id = entity_id
        self.update_entity(entity)
        return entity

    def update_entity(self, entity: Entity) -> Entity:
        assert entity.entity_id
        pipeline = self.redis.pipeline()
        entity_updates = {c.key: c.value for c in entity.pending_changes.values()}
        pipeline.hmset(
            '{}:{}'.format(self._entity_prefix, entity.entity_id),
            entity_updates
        )
        components_updates = {}
        for c in entity.pending_changes.values():
            pipeline.setbit(
                '{}:{}:{}'.format(self._component_prefix, c.key, self._map_suffix),
                entity.entity_id,
                c.is_active()
            )
            components_updates[c.key] = {entity.entity_id: c.value}
            pipeline.hmset(
                '{}:{}:{}'.format(self._component_prefix, c.key, self._data_suffix),
                components_updates[c.key]
            )
        response = pipeline.execute()
        entity.pending_changes.clear()
        LOGGER.core.debug(
            'EntityRepository.update_entity_components(%s, %s), response: %s',
            entity.entity_id, entity_updates, response
        )
        return response

    def get_components_values_per_entity(
            self, entity_id: int, *components: ComponentType
    ) -> typing.List[typing.Optional[bytes]]:
        response = self.redis.hmget('{}:{}'.format(self._entity_prefix, entity_id), (c.key for c in components))
        LOGGER.core.debug(
            'EntityRepository.get_components_values_per_entity(%s, %s), response: %s',
            entity_id, components, response
        )
        return response

    def get_components_values_per_entities(
            self, entities: typing.List[int], components: typing.List[ComponentType]
    ) -> typing.List[typing.Optional[bytes]]:
        pipeline = self.redis.pipeline()
        for c in components:
            pipeline.hmget(
                self._component_prefix + ':' + c.key + ':' + self._data_suffix,
                entities
            )
        response = pipeline.execute()
        return response

    def get_entity_ids_with_components(self, *components: ComponentType) -> typing.Iterator[int]:
        _key = binascii.hexlify(os.urandom(8))
        self.redis.bitop('AND', _key, *(c.key for c in components))
        p = self.redis.pipeline()
        self.redis.get(_key)
        self.redis.delete(_key)
        bitmap, _ = p.execute()
        return (i for i, v in enumerate(bitarray.bitarray().frombytes(bitmap)) if v)
