import asyncio
import typing
from ast import literal_eval
from collections import OrderedDict

import aioredis
import bitarray
import os
from core.src.auth.logging_factory import LOGGER
from core.src.world.components import ComponentType, ComponentTypeEnum
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.factory import get_component_alias_by_enum_value
from core.src.world.components.instance_of import InstanceOfComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.domain.room import Room
from core.src.world.domain.entity import Entity, EntityID
from core.src.world.repositories.library_repository import RedisLibraryRepository
from core.src.world.repositories.map_repository import RedisMapRepository
from core.src.world.utils.world_types import Bit, EvaluatedEntity


class RedisDataRepository:
    def __init__(
            self,
            async_redis_factory,
            library_repository: RedisLibraryRepository,
            map_repository: RedisMapRepository
    ):
        self._async_redis_factory = async_redis_factory
        self.library_repository = library_repository
        self.map_repository = map_repository
        self._entity_prefix = 'e'
        self._component_prefix = 'c'
        self._map_suffix = 'm'
        self._map_prefix = 'm'
        self._data_suffix = 'd'
        self._room_content_suffix = 'c'
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
                await (await self._async_redis).setbit('{}:{}'.format(
                    self._entity_prefix,
                    self._map_suffix
                ), 0, 1
                )  # ensure the map is 1 based
        finally:
            self.async_lock.release()
        return self._async_redis

    async def _allocate_entity_id(self) -> int:
        script = """
            local val = redis.call('bitpos', '{0}:{1}', 0)
            redis.call('setbit', '{0}:{1}', val, 1)
            return val
            """\
            .format(self._entity_prefix, self._map_suffix)
        redis = await self.async_redis()
        response = await redis.eval(script, ['{}:{}'.format(self._entity_prefix, self._map_prefix)])
        LOGGER.core.debug('EntityRepository.create_entity, response: %s', response)
        assert response
        return int(response)

    async def entity_exists(self, entity_id):
        redis = await self.async_redis()
        return bool(await redis.keys('{}:{}'.format(self._entity_prefix, entity_id)))

    def _update_map_position_for_entity(self, position: PosComponent, entity: Entity, pipeline):
        # TODO FIXME - use smove in the future, with a clean bootstrap
        if position.previous_position:
            prev_set_name = self.get_room_key(
                position.previous_position.x,
                position.previous_position.y,
                position.previous_position.z
            )
            pipeline.srem(prev_set_name, '{}'.format(entity.entity_id))
        if position.value:
            new_set_name = self.get_room_key(position.x, position.y, position.z)
            pipeline.sadd(new_set_name, '{}'.format(entity.entity_id))

    async def save_entity(self, entity: Entity) -> Entity:
        assert not entity.entity_id, 'entity_id: %s, use update, not save.' % entity.entity_id
        entity_id = await self._allocate_entity_id()
        entity.entity_id = EntityID(entity_id)
        await self.update_entities(entity)
        return entity

    async def update_entities(self, *entities: Entity) -> Entity:
        redis = await self.async_redis()
        pipeline = redis.pipeline()
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
            pipeline.hmset_dict('{}:{}'.format(self._entity_prefix, up_en_id), _up_values_by_en)

        for up_c_key, _up_values_by_comp in components_updates.items():
            pipeline.hmset_dict(
                '{}:{}:{}'.format(self._component_prefix, up_c_key, self._data_suffix),
                _up_values_by_comp
            )

        for del_c_key, _del_entities in deletions_by_component.items():
            pipeline.hdel('{}:{}:{}'.format(self._component_prefix, del_c_key, self._data_suffix), *_del_entities)

        for _del_en_id, _del_components in deletions_by_entity.items():
            pipeline.hdel('{}:{}'.format(self._entity_prefix, _del_en_id), *_del_components)

        response = await pipeline.execute()
        for entity in entities:
            entity.pending_changes.clear()

        LOGGER.core.debug('EntityRepository.update_entity_components, response: %s', response)
        return response

    async def get_component_value_by_entity_id(self, entity_id: int, component: typing.Type[ComponentType])\
             -> typing.Optional[ComponentType]:
        redis = await self.async_redis()
        res = await redis.hmget(
            '{}:{}'.format(self._entity_prefix, entity_id),
            InstanceOfComponent.key, component.key
        )
        if not res:
            return
        if not res[1]:
            if component in (PosComponent, ConnectionComponent):
                # Fixme
                return
            if not res[0]:
                # Todo - Remove once all the entities are fixed with a proper InstanceOf
                LOGGER.core.error('Entity id {} has not InstanceOfComponent'.format(entity_id))
                return
            return self.library_repository.get_defaults_for_library_element(res[0].decode(), component)
        return res and component(component.cast_type(res[1]))

    async def get_components_values_by_entities(
            self,
            entities: typing.List[Entity],
            components: typing.List[typing.Type[ComponentType]]
    ) -> typing.Dict[EntityID, typing.Dict[ComponentTypeEnum, bytes]]:
        _bits_statuses = await self._get_components_statuses_by_entities(entities, components)
        _filtered = await self._get_components_values_from_entities_storage(_bits_statuses)
        return {
            e.entity_id: {
                c.component_enum: c.cast_type(_filtered.get(e.entity_id, {}).get(c.key)) for c in components
            } for e in entities
        }

    async def get_raw_component_value_by_entity_ids(
            self, component, *entity_ids: int):
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for entity_id in entity_ids:
            key = '{}:{}'.format(self._entity_prefix, entity_id)
            pipeline.hmget(key, InstanceOfComponent.key, component.key)
        results = await pipeline.execute()
        response = []
        for result in results:
            if result[1]:
                response.append(result[1].decode())
            else:
                v = self.library_repository.get_defaults_for_library_element(
                    result[0].decode(), component
                )
                response.append(v and v.value or v)
        return response

    async def get_components_values_by_components(
            self,
            entity_ids: typing.List[int],
            components: typing.List[typing.Type[ComponentType]]
    ) -> typing.Dict[ComponentTypeEnum, typing.Dict[EntityID, bytes]]:
        _bits_statuses = await self._get_components_statuses_by_components(entity_ids, components)
        _filtered = await self._get_components_values_from_components_storage(_bits_statuses)
        s = {
            ComponentTypeEnum(c.key): {
                entity_id: c.cast_type(_filtered.get(c.key, {}).get(entity_id)) for entity_id in entity_ids
            } for c in components}
        return s

    async def _get_components_statuses_by_entities(
            self,
            entities: typing.List[Entity],
            components: typing.List[typing.Type[ComponentType]]
    ) -> OrderedDict:
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        bits_by_entity = OrderedDict()
        for _e in entities:
            for _c in components:
                key = '{}:{}:{}'.format(self._component_prefix, _c.key, self._map_suffix)
                pipeline.getbit(key, _e.entity_id)
        data = await pipeline.execute()
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

    async def _get_components_statuses_by_components(
            self,
            entities: typing.List[int],
            components: typing.List[typing.Type[ComponentType]]
    ) -> OrderedDict:
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        bits_by_component = OrderedDict()
        for _c in components:
            for _e in entities:
                pipeline.getbit('{}:{}:{}'.format(self._component_prefix, _c.key, self._map_suffix), _e)
        data = await pipeline.execute()
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

    async def get_entity_ids_with_components(self, *components: ComponentType) -> typing.Iterator[int]:
        _key = os.urandom(8)
        redis = await self.async_redis()
        await redis.bitop_and(
            _key,
            *('{}:{}:{}'.format(self._component_prefix, c.key, self._map_suffix) for c in components)
        )
        p = redis.pipeline()
        p.get(_key)
        p.delete(_key)
        res = await p.execute()
        bitmap, _ = res
        array = bitarray.bitarray()
        bitmap and array.frombytes(bitmap) or []
        return (i for i, v in enumerate(array) if v)

    async def _get_components_values_from_components_storage(self, filtered_query: OrderedDict):
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for c_key in filtered_query:
            keys = [
                ent_id for ent_id, status_and_querable in filtered_query[c_key].items()
                if all(status_and_querable)
            ]
            if keys:
                pipeline.hget(
                    '{}:{}:{}'.format(self._component_prefix, InstanceOfComponent.key, self._data_suffix),
                    *keys
                )
                pipeline.hmget(
                    '{}:{}:{}'.format(self._component_prefix, c_key, self._data_suffix),
                    *keys
                )
        entities_instance_of = []
        response = []
        redis_response = await pipeline.execute()

        for i, element in enumerate(redis_response):
            if not i % 2:
                entities_instance_of.append(element)
            else:
                response.append(element)
        data = {}
        i = 0
        for c_key, value in filtered_query.items():
            e_i = 0
            for entity_id, status in value.items():
                if not status[1]:
                    value = status[0] or self.library_repository.get_defaults_for_library_element(
                        entities_instance_of[i].decode(),
                        get_component_alias_by_enum_value(ComponentTypeEnum(c_key))
                    )
                    value = value.value if (not status[0] and value) else value
                    try:
                        data[ComponentTypeEnum(c_key)].update({EntityID(entity_id): value})
                    except KeyError:
                        data[ComponentTypeEnum(c_key)] = {EntityID(entity_id): value}
                elif all(status):
                    value = response[i][e_i] or self.library_repository.get_defaults_for_library_element(
                        entities_instance_of[i].decode(),
                        get_component_alias_by_enum_value(ComponentTypeEnum(c_key))
                    )
                    value = value.value if (not response[i][e_i] and value) else value
                    try:
                        data[ComponentTypeEnum(c_key)].update({EntityID(entity_id): value})
                    except KeyError:
                        data[ComponentTypeEnum(c_key)] = {EntityID(entity_id): value}
                    except IndexError:
                        raise
                    e_i += 1
            i += 1
        return data

    async def _get_components_values_from_entities_storage(self, filtered_query: OrderedDict):
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for entity_id, value in filtered_query.items():
            keys = [InstanceOfComponent.key] + [
                comp_key for comp_key, status_and_querable in value.items() if all(status_and_querable)
            ]
            pipeline.hmget('{}:{}'.format(self._entity_prefix, entity_id), *keys)
        response = await pipeline.execute()
        data = {}
        i = 0
        for entity_id, value in filtered_query.items():
            c_i = 1   # 1-based cause the element 0 is InstanceOf
            for c_key, status in value.items():
                if not status[1]:
                    value = status[0] or self.library_repository.get_defaults_for_library_element(
                        response[i][0].decode(), get_component_alias_by_enum_value(ComponentTypeEnum(c_key))
                    )
                    value = value.value if (not status[0] and value) else value
                    try:
                        data[EntityID(entity_id)].update({ComponentTypeEnum(c_key): value})
                    except KeyError:
                        data[EntityID(entity_id)] = {ComponentTypeEnum(c_key): value}
                elif all(status):
                    value = response[i][c_i] or self.library_repository.get_defaults_for_library_element(
                        response[i][0].decode(), get_component_alias_by_enum_value(ComponentTypeEnum(c_key))
                    )
                    value = value.value if (not response[i][c_i] and value) else value
                    try:
                        data[EntityID(entity_id)].update({ComponentTypeEnum(c_key): value})
                    except KeyError:
                        data[EntityID(entity_id)] = {ComponentTypeEnum(c_key): value}
                    c_i += 1
            i += 1
        return data

    async def get_entities_evaluation_by_entity(
            self, entity: Entity, *entity_ids: int
    ) -> typing.List[EvaluatedEntity]:
        result = []
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for entity_id in entity_ids:
            pipeline.hmget(
                '{}:{}'.format(self._entity_prefix, entity_id),
                InstanceOfComponent.key, AttributesComponent.key,
            )
        data = await pipeline.execute()
        for i, el in enumerate(data):
            if el[1]:
                attrs = AttributesComponent.from_bytes(el[1])
            else:
                attrs = self.library_repository.get_defaults_for_library_element(
                    el[0].decode(), AttributesComponent
                )
            result.append(
                EvaluatedEntity(
                    name=attrs.name,
                    type=0,
                    status=0,
                    known=True,
                    excerpt="<placeholder for short description>",
                    entity_id=entity_ids[i]
                )
            )
        return result

    async def populate_area_content_for_area(self, entity: Entity, area: Area) -> None:
        # TODO FIXME
        for _room in area.rooms:
            if _room:
                for _entity_id in _room.entity_ids:
                    evaluated_entity = EvaluatedEntity(
                        type=0,
                        status=0,
                        entity_id=_entity_id,
                        name='',
                        excerpt='',
                        known=False
                    )
                    entity.can_see_evaluated_entity(evaluated_entity) and _room.add_evaluated_entity(evaluated_entity)

    async def populate_room_content_for_look(self, entity: Entity, room: Room):
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        _exp_res = []
        for entity_id in room.entity_ids:
            if entity_id == entity.entity_id:
                continue
            pipeline.hmget(
                '{}:{}'.format(self._entity_prefix, entity_id),
                InstanceOfComponent.key, AttributesComponent.key
            )
            _exp_res.append(entity_id)
        result = await pipeline.execute()
        for i, _entity_id in enumerate(_exp_res):
            try:
                if result[i][1]:
                    attrs = AttributesComponent.from_bytes(result[i][1])
                else:
                    if not result[i][0]:
                        # FIXME REMOVE TODO
                        LOGGER.core.error('Entity id {} has not InstanceOfComponent'.format(_entity_id))
                        attrs = None
                    else:
                        attrs = self.library_repository.get_defaults_for_library_element(
                            result[i][0].decode(), AttributesComponent
                        )
            except Exception as e:
                raise ValueError('Errorone! i: {} entity_id: {}'.format(i, _entity_id)) from e
            evaluated_entity = EvaluatedEntity(
                name=attrs and attrs.name,
                type=0,
                status=0,
                entity_id=_entity_id,
                known=True,
                excerpt="<placeholder for short description>"
            )
            entity.can_see_evaluated_entity(evaluated_entity) and room.add_evaluated_entity(evaluated_entity)

    async def get_raw_content_for_room_interaction(self, entity_id: int, room: Room) -> (int, typing.Generator):
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        _exp_res = []
        for look_at_entity_id in room.entity_ids:
            if look_at_entity_id == entity_id:
                continue
            pipeline.hmget(
                '{}:{}'.format(self._entity_prefix, look_at_entity_id),
                InstanceOfComponent.key, AttributesComponent.key
            )
            _exp_res.append(look_at_entity_id)
        result = await pipeline.execute()

        def _parse_data(res_entry):
            if res_entry[1]:
                return [
                    res_entry[1] and literal_eval(res_entry[1].decode()) or {}
                ]
            else:
                return [
                    self.library_repository.get_defaults_for_library_element(
                        res_entry[0].decode(), AttributesComponent
                    ).value
                ]
        res = [{'entity_id': entity_id, 'data': _parse_data(result[i])} for i, entity_id in enumerate(_exp_res)]
        return 1, res

    async def get_look_components_for_entity_id(self, entity_id):
        redis = await self.async_redis()
        data = await redis.hmget(
            '{}:{}'.format(self._entity_prefix, entity_id),
            InstanceOfComponent.key, AttributesComponent.key
        )
        if not data[1]:
            attributes = self.library_repository.get_defaults_for_library_element(
                data[0].decode(), AttributesComponent
            )
        else:
            attributes = AttributesComponent.from_bytes(data[1])
        return {
            'name': attributes.name,
            'known': True,
            'type': 0,
            'status': 0,
            'description': attributes.description
        }

    async def delete_entity(self, entity_id: int):
        redis = await self.async_redis()
        components = await redis.hgetall('{}:{}'.format(self._entity_prefix, entity_id))
        pipeline = redis.pipeline()
        pipeline.delete('{}:{}'.format(self._entity_prefix, entity_id))
        for k, v in components.items():
            k = k.decode()
            try:
                if int(k) == PosComponent.key:
                    await self.map_repository.remove_entity_from_map(
                        entity_id, PosComponent.from_bytes(v), pipeline=pipeline
                    )
            except Exception:
                LOGGER.core.error('Cannot remove instance from position {}. Must do a manual cleanup'.format(v))
            pipeline.hdel('{}:{}:{}'.format(self._component_prefix, k, self._data_suffix), entity_id)
            pipeline.setbit(
                '{}:{}:{}'.format(self._component_prefix, k, self._map_suffix), entity_id, Bit.OFF.value
            )
        await pipeline.execute()
        return True
