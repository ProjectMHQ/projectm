import typing
import binascii
import bitarray
import os
from redis import StrictRedis
from core.src.logging_factory import LOGGER
from core.src.world.components import ComponentType, ComponentTypeEnum
from core.src.world.entity import Entity, EntityID
from core.src.world.types import Bit


class RedisDataRepository:
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
        entity.entity_id = EntityID(entity_id)
        self.update_entities(entity)
        return entity

    def update_entities(self, *entities: Entity) -> Entity:
        pipeline = self.redis.pipeline()
        entities_updates = {}
        components_updates = {}
        deletions_by_component = {}
        deletions_by_entity = {}
        for entity in entities:
            assert entity.entity_id
            for c in entity.pending_changes.values():
                pipeline.setbit(
                    '{}:{}:{}'.format(self._component_prefix, c.key, self._map_suffix),
                    entity.entity_id, c.is_active() and Bit.ON.value or Bit.OFF.value
                )
                if c.has_data() and not c.has_operation():
                    LOGGER.core.debug('Absolute value, component data set')
                    _comp_v = {entity.entity_id: c.value}
                    _ent_v = {c.key: c.value}
                    try:
                        components_updates[c.key].update(_comp_v)
                    except KeyError:
                        components_updates[c.key] = _comp_v
                    try:
                        entities_updates[entity.entity_id].update(_ent_v)
                    except KeyError:
                        entities_updates[entity.entity_id] = _ent_v
                elif c.has_data():
                    LOGGER.core.debug('Relative value, component data incr')
                    assert c.component_type == int
                    pipeline.hincrby(
                        '{}:{}:{}'.format(self._component_prefix, c.key, self._data_suffix),
                        entity.entity_id, int(c.operation)
                    )
                    pipeline.hincrby(
                        '{}:{}'.format(self._entity_prefix, entity.entity_id),
                        c.key, int(c.operation)
                    )
                else:
                    try:
                        deletions_by_component[c.key].append(entity.entity_id)
                    except KeyError:
                        deletions_by_component[c.key] = [entity.entity_id]
                    try:
                        deletions_by_entity[entity.entity_id].append(c.key)
                    except KeyError:
                        deletions_by_entity[entity.entity_id] = c.key
                    LOGGER.core.debug('No data to set')
                LOGGER.core.debug(
                    'EntityRepository.update_entity_components. ids: %s, updates: %s, deletions: %s)',
                    entity.entity_id, entities_updates[entity.entity_id], deletions_by_entity[entity.entity_id]
                )
        for up_en_id, _up_values_by_en in entities_updates.items():
            pipeline.hmset('{}:{}'.format(self._entity_prefix, up_en_id), _up_values_by_en)

        for up_c_key, _up_values_by_comp in components_updates.items():
            pipeline.hmset(
                '{}:{}:{}'.format(self._component_prefix, up_c_key, self._data_suffix),
                _up_values_by_comp
            )

        for del_c_key, _del_entities in deletions_by_component.items():
            pipeline.hdel('{}:{}:{}'.format(self._component_prefix, del_c_key, self._data_suffix), *_del_entities)

        for _del_en_id, _del_components in deletions_by_entity.items():
            pipeline.hdel('{}:{}'.format(self._entity_prefix, _del_en_id), *_del_components)

        response = pipeline.execute()
        for entity in entities:
            entity.pending_changes.clear()

        LOGGER.core.debug('EntityRepository.update_entity_components, response: %s', response)
        return response

    def get_components_values_by_entities(
            self,
            entities: typing.List[Entity],
            components: typing.List[ComponentType]
    ) -> typing.Dict[EntityID, typing.Dict[ComponentTypeEnum, bytes]]:
        _filtered = self._get_components_statuses_by_entities(entities, components)
        return self._get_components_values_from_entities_storage(_filtered)

    def get_components_values_by_components(
            self,
            entities: typing.List[Entity],
            components: typing.List[ComponentType]
    ) -> typing.Dict[ComponentTypeEnum, typing.Dict[EntityID, bytes]]:
        _filtered = self._get_components_statuses_by_components(entities, components)
        return self._get_components_values_from_components_storage(_filtered)

    def _get_components_statuses_by_entities(
            self,
            entities: typing.List[Entity],
            components: typing.List[ComponentType]
    ) -> typing.Dict:
        pipeline = self.redis.pipeline()
        data_by_entity = {}
        # FIXME TODO - Think about that.
        for _c in components:
            for _e in entities:
                pipeline.getbit('{}:{}:{}'.format(self._component_prefix, _c, self._map_suffix), _e)
        data = pipeline.execute()
        i = 0
        for comp in components:
            for ent in entities:
                _ent_v = {comp.key: data[i]}
                try:
                    data_by_entity[ent.entity_id].update(_ent_v)
                except KeyError:
                    data_by_entity[ent.entity_id] = _ent_v
        return data_by_entity

    def _get_components_statuses_by_components(
            self,
            entities: typing.List[Entity],
            components: typing.List[ComponentType]
    ) -> typing.Dict:
        pipeline = self.redis.pipeline()
        data_by_component = {}
        for _c in components:
            for _e in entities:  # same
                pipeline.getbit('{}:{}:{}'.format(self._component_prefix, _c.key, self._map_suffix), _e.entity_id)
        data = pipeline.execute()
        i = 0
        for comp in components:
            for ent in entities:
                _comp_v = {ent.entity_id: data[i]}
                try:
                    data_by_component[comp.key].update(_comp_v)
                except KeyError:
                    data_by_component[comp.key] = _comp_v
                i += 1
        return data_by_component

    def get_entity_ids_with_components(self, *components: ComponentType) -> typing.Iterator[int]:
        _key = binascii.hexlify(os.urandom(8))
        self.redis.bitop('AND', _key, *(c.key for c in components))
        p = self.redis.pipeline()
        self.redis.get(_key)
        self.redis.delete(_key)
        bitmap, _ = p.execute()
        return (i for i, v in enumerate(bitarray.bitarray().frombytes(bitmap)) if v)

    def _get_components_values_from_components_storage(self, filtered_query: typing.Dict):
        pipeline = self.redis.pipeline()
        for c_key in filtered_query:
            pipeline.hmget(
                '{}:{}:{}'.format(self._component_prefix, c_key, self._data_suffix),
                *(ent_id for ent_id, status in filtered_query[c_key].items() if status)
            )
        response = pipeline.execute()
        return response

    def _get_components_values_from_entities_storage(self, filtered_query: typing.Dict):
        pipeline = self.redis.pipeline()
        for entity_id in filtered_query.items():
            pipeline.hmget(
                '{}:{}'.format(self._entity_prefix, entity_id),
                *(comp_key for comp_key, status in filtered_query[entity_id].items() if status)
            )
        response = pipeline.execute()
        return response

