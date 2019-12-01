import asyncio
import struct
import typing
from collections import OrderedDict

import aioredis
import bitarray
import os
from redis import StrictRedis
from core.src.auth.logging_factory import LOGGER
from core.src.world.components import ComponentType, ComponentTypeEnum
from core.src.world.components.name import NameComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.entity import Entity, EntityID
from core.src.world.utils.world_types import Bit, EvaluatedEntity


class RedisDataRepository:
    def __init__(self, redis: StrictRedis, async_redis_factory):
        self._async_redis_factory = async_redis_factory
        self.redis = redis
        self._entity_prefix = 'e'
        self._component_prefix = 'c'
        self._map_suffix = 'm'
        self._map_prefix = 'm'
        self._data_suffix = 'd'
        self._room_content_suffix = 'c'
        redis.setbit('{}:{}'.format(self._entity_prefix, self._map_suffix), 0, 1)  # ensure the map is 1 based
        self.async_lock = asyncio.Lock()
        self._async_redis = None
        self.room_content_key = '{}:{}:{}'.format(self._map_prefix, '{}', self._room_content_suffix)

    def get_room_key(self, x, y, z):
        if z:
            return self.room_content_key.format('{}.{}.{}'.format(x, y, z))
        else:
            return self.room_content_key.format('{}.{}'.format(x, y))

    async def async_redis(self) -> aioredis.Redis:
        await self.async_lock.acquire()
        try:
            if not self._async_redis:
                self._async_redis = await self._async_redis_factory()
        finally:
            self.async_lock.release()
        return self._async_redis

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

    def _update_map_position_for_entity(self, position: PosComponent, entity: Entity, pipeline):
        assert position.has_previous_position()
        prev = position.previous_position
        prev_set_name = self.get_room_key(prev.x, prev.y, prev.z)
        new_set_name = self.get_room_key(position.x, position.y, position.z)
        # TODO FIXME - use smove in the future, with a clean bootstrap
        pipeline.srem(prev_set_name, '{}'.format(entity.entity_id))
        pipeline.sadd(new_set_name, '{}'.format(entity.entity_id))

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
                if c.component_enum == ComponentTypeEnum.POS:
                    self._update_map_position_for_entity(c, entity, pipeline)
                pipeline.setbit(
                    '{}:{}:{}'.format(self._component_prefix, c.key, self._map_suffix),
                    entity.entity_id, Bit.ON.value if c.is_active() else Bit.OFF.value
                )
                if c.has_data() and not c.has_operation():
                    LOGGER.core.debug('Absolute value, component data set')
                    _comp_v = {entity.entity_id: c.serialized}
                    _ent_v = {c.key: c.serialized}
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
                elif c.is_active():
                    LOGGER.core.debug('No data to set')
                else:
                    LOGGER.core.debug('Data to delete')
                    try:
                        deletions_by_component[c.key].append(entity.entity_id)
                    except KeyError:
                        deletions_by_component[c.key] = [entity.entity_id]
                    try:
                        deletions_by_entity[entity.entity_id].append(c.key)
                    except KeyError:
                        deletions_by_entity[entity.entity_id] = [c.key]
                LOGGER.core.debug(
                    'EntityRepository.update_entity_components. ids: %s, updates: %s, deletions: %s)',
                    entity.entity_id, entities_updates.get(entity.entity_id), deletions_by_entity.get(entity.entity_id)
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

    def get_component_value_by_entity_id(self, entity_id: int, component: typing.Type[ComponentType]):
        res = self.redis.hget(
            '{}:{}'.format(self._entity_prefix, entity_id),
            component.key
        )
        return res and component(component.cast_type(res))

    def get_components_values_by_entities(
            self,
            entities: typing.List[Entity],
            components: typing.List[typing.Type[ComponentType]]
    ) -> typing.Dict[EntityID, typing.Dict[ComponentTypeEnum, bytes]]:
        _bits_statuses = self._get_components_statuses_by_entities(entities, components)
        _filtered = self._get_components_values_from_entities_storage(_bits_statuses)
        return {
            e.entity_id: {
                c.component_enum: c.cast_type(_filtered.get(e.entity_id, {}).get(c.key)) for c in components
            } for e in entities
        }

    def get_raw_component_value_by_entity_ids(
            self, component, *entity_ids: int):
        pipeline = self.redis.pipeline()
        for entity_id in entity_ids:
            key = '{}:{}'.format(self._entity_prefix, entity_id)
            pipeline.hget(key, component.key)
        results = pipeline.execute()
        return (x.decode() for x in results if x)

    def get_components_values_by_components(
            self,
            entity_ids: typing.List[int],
            components: typing.List[typing.Type[ComponentType]]
    ) -> typing.Dict[ComponentTypeEnum, typing.Dict[EntityID, bytes]]:
        _bits_statuses = self._get_components_statuses_by_components(entity_ids, components)
        _filtered = self._get_components_values_from_components_storage(_bits_statuses)
        s = {
            ComponentTypeEnum(c.key): {
                entity_id: c.cast_type(_filtered.get(c.key, {}).get(entity_id)) for entity_id in entity_ids
            } for c in components}
        return s

    def _get_components_statuses_by_entities(
            self,
            entities: typing.List[Entity],
            components: typing.List[typing.Type[ComponentType]]
    ) -> OrderedDict:
        pipeline = self.redis.pipeline()
        bits_by_entity = OrderedDict()
        for _e in entities:
            for _c in components:
                key = '{}:{}:{}'.format(self._component_prefix, _c.key, self._map_suffix)
                pipeline.getbit(key, _e.entity_id)
        data = pipeline.execute()
        i = 0
        for ent in entities:
            for comp in components:
                _ent_v = {comp.key: [data[i], comp.component_type != bool]}
                try:
                    bits_by_entity[ent.entity_id].update(_ent_v)
                except KeyError:
                    bits_by_entity[ent.entity_id] = _ent_v
                i += 1
        return bits_by_entity

    def _get_components_statuses_by_components(
            self,
            entities: typing.List[int],
            components: typing.List[typing.Type[ComponentType]]
    ) -> OrderedDict:
        pipeline = self.redis.pipeline()
        bits_by_component = OrderedDict()
        for _c in components:
            for _e in entities:
                pipeline.getbit('{}:{}:{}'.format(self._component_prefix, _c.key, self._map_suffix), _e)
        data = pipeline.execute()
        i = 0
        for comp in components:
            for ent in entities:
                _comp_v = {ent: [data[i], comp.component_type != bool]}
                try:
                    bits_by_component[comp.key].update(_comp_v)
                except KeyError:
                    bits_by_component[comp.key] = _comp_v
                i += 1
        return bits_by_component

    def get_entity_ids_with_components(self, *components: ComponentType) -> typing.Iterator[int]:
        _key = os.urandom(8)
        self.redis.bitop(
            'AND',
            _key,
            *('{}:{}:{}'.format(self._component_prefix, c.key, self._map_suffix) for c in components)
        )
        p = self.redis.pipeline()
        p.get(_key)
        p.delete(_key)
        res = p.execute()
        bitmap, _ = res
        array = bitarray.bitarray()
        bitmap and array.frombytes(bitmap) or []
        return (i for i, v in enumerate(array) if v)

    def _get_components_values_from_components_storage(self, filtered_query: OrderedDict):
        pipeline = self.redis.pipeline()
        for c_key in filtered_query:
            keys = [
                ent_id for ent_id, status_and_querable in filtered_query[c_key].items()
                if all(status_and_querable)
            ]
            if keys:
                pipeline.hmget('{}:{}:{}'.format(self._component_prefix, c_key, self._data_suffix), *keys)
        response = pipeline.execute()
        data = {}
        i = 0
        for c_key, value in filtered_query.items():
            e_i = 0
            for entity_id, status in value.items():
                if not status[1]:
                    try:
                        data[ComponentTypeEnum(c_key)].update({EntityID(entity_id): status[0] or None})
                    except KeyError:
                        data[ComponentTypeEnum(c_key)] = {EntityID(entity_id): status[0] or None}
                elif all(status):
                    try:
                        data[ComponentTypeEnum(c_key)].update({EntityID(entity_id): response[i][e_i]})
                    except KeyError:
                        data[ComponentTypeEnum(c_key)] = {EntityID(entity_id): response[i][e_i]}
                    except IndexError:
                        raise
                    e_i += 1
            i += 1
        return data

    def _get_components_values_from_entities_storage(self, filtered_query: OrderedDict):
        pipeline = self.redis.pipeline()
        for entity_id, value in filtered_query.items():
            keys = [comp_key for comp_key, status_and_querable in value.items() if all(status_and_querable)]
            if keys:
                pipeline.hmget('{}:{}'.format(self._entity_prefix, entity_id), *keys)
        response = pipeline.execute()
        data = {}
        i = 0
        for entity_id, value in filtered_query.items():
            c_i = 0
            for c_key, status in value.items():
                if not status[1]:
                    try:
                        data[EntityID(entity_id)].update({ComponentTypeEnum(c_key): status[0] or None})
                    except KeyError:
                        data[EntityID(entity_id)] = {ComponentTypeEnum(c_key): status[0] or None}
                elif all(status):
                    try:
                        data[EntityID(entity_id)].update({ComponentTypeEnum(c_key): response[i][c_i]})
                    except KeyError:
                        data[EntityID(entity_id)] = {ComponentTypeEnum(c_key): response[i][c_i]}
                    c_i += 1
            i += 1
        return data

    async def get_entities_evaluation_by_entity(self, entity: Entity, *entity_ids: int) -> typing.List[EvaluatedEntity]:
        result = []
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for entity_id in entity_ids:
            pipeline.hmget(
                '{}:{}'.format(self._entity_prefix, entity_id),
                NameComponent.key,
            )
        data = await pipeline.execute()
        for i, el in enumerate(data):
            result.append(
                EvaluatedEntity(
                    name=el[0].decode(),
                    type=0,
                    status=0,
                    known=True,
                    excerpt="un brutto ceffo dall'aspetto elegante",
                    entity_id=entity_ids[i]
                )
            )
        return result

    async def populate_area_content_for_entity(self, entity: Entity, area: Area) -> None:
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for room in area.rooms:
            if room:
                for entity_id in room.entity_ids:
                    pipeline.hmget(
                        '{}:{}'.format(self._entity_prefix, entity_id),
                        NameComponent.key, b'a', b'b'
                    )
        result = await pipeline.execute()
        i = 0
        for _room in area.rooms:
            if _room:
                for _entity_id in _room.entity_ids:
                    _evaluated_entity_response = result[i]
                    evaluated_entity = EvaluatedEntity(
                        name=_evaluated_entity_response[0].decode(),
                        type=0,
                        status=0,
                        known=True,
                        excerpt="un brutto ceffo dall'aspetto elegante",
                        entity_id=_entity_id
                    )
                    entity.can_see_evaluated_entity(evaluated_entity) and _room.add_evaluated_entity(evaluated_entity)
                    i += 1
