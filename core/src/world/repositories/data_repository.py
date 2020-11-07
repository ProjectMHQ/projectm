import asyncio
import inspect
import time
import typing
from collections import OrderedDict

import aioredis
import bitarray
import os
from core.src.auth.logging_factory import LOGGER
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.base import ComponentType, ComponentTypeEnum
from core.src.world.components.base.structcomponent import StructSubtypeListAction, StructSubtypeStrSetAction, \
    StructSubtypeIntIncrAction, StructSubtypeIntSetAction, StructSubTypeSetNull, StructSubTypeBoolOn, \
    StructSubTypeBoolOff, StructSubTypeDictSetKeyValueAction, \
    StructSubTypeDictRemoveKeyValueAction, StructComponent, load_value_in_struct_component
from core.src.world.components.factory import get_component_by_enum_value, get_component_alias_by_enum_value
from core.src.world.components.pos import PosComponent
from core.src.world.components.system import SystemComponent
from core.src.world.domain.area import Area
from core.src.world.domain.room import Room
from core.src.world.domain.entity import Entity
from core.src.world.repositories.library_repository import RedisLibraryRepository
from core.src.world.repositories.map_repository import RedisMapRepository
from core.src.world.repositories.redis_lua_pipeline import RedisLUAPipeline
from core.src.world.utils.world_types import Bit


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
        self._zset_suffix = 'zs'
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

    async def save_entity(self, entity: Entity) -> Entity:
        assert not entity.entity_id, 'entity_id: %s, use update, not save.' % entity.entity_id
        entity_id = await self._allocate_entity_id()
        entity.entity_id = entity_id
        await self.update_entities(entity)
        return entity

    def _check_bounds_for_update(self, pipeline: RedisLUAPipeline, entity: Entity):
        for bound in entity.bounds():
            if bound.is_struct:
                assert bound.bounds
                for k, bb in bound.bounds.items():
                    for b in bb:
                        if isinstance(b, StructSubtypeListAction):
                            assert b.type == 'remove'
                            key = 'c:{}:zs:e:{}:{}'.format(bound.enum, entity.entity_id, k)
                            values = b.values
                            if len(values) == 1:
                                pipeline.allocate_value().zscan(key, cursor=0, match=values[0])
                                v, check = "[2][1]", str(values[0])
                            else:
                                inter_seed = pipeline.zprepareinter(key, values)
                                pipeline.allocate_value().zfetchinter(inter_seed)
                                v, check = "", values
                            pipeline.add_if_equal(check, value_selector=v)
                        else:
                            raise ValueError('Unknown bound')
                    bound.remove_bounds()
            elif bound.is_array():
                assert bound.bounds
                key = '{}:{}:{}:{}'.format(
                    self._component_prefix, bound.key, self._zset_suffix, entity.entity_id
                )
                if len(bound.bounds) == 1:
                    pipeline.allocate_value().zscan(key, cursor=0, match=bound.bounds[0])
                    v, check = "[2][1]", str(bound.bounds[0])
                else:
                    inter_seed = pipeline.zprepareinter(key, bound.bounds)
                    pipeline.allocate_value().zfetchinter(inter_seed)
                    v, check = "", bound.bounds
                pipeline.add_if_equal(check, value_selector=v)
            else:
                pipeline.allocate_value().hget('e:{}'.format(entity.entity_id), bound.key)
                pipeline.add_if_equal(str(bound.value))

    def _update_array_for_entity(self, pipeline, entity, component):
        payload = []
        if component.to_add:
            for x in component.to_add:
                payload.extend([int(time.time()*100000), x])
            pipeline.zadd(
                '{}:{}:{}:{}'.format(self._component_prefix, component.key, self._zset_suffix, entity.entity_id),
                *payload
            )
        component.to_remove and pipeline.zrem(
            '{}:{}:{}:{}'.format(self._component_prefix, component.key, self._zset_suffix, entity.entity_id),
            *component.to_remove
        )

    @staticmethod
    def _batch_component_for_update(components_updates_queue, entities_updates_queue, entity, component):
        LOGGER.core.debug('Absolute value, component data set')
        _comp_v = {entity.entity_id: component.serialized}
        _ent_v = {component.key: component.serialized}
        try:
            components_updates_queue[component.key].update(_comp_v)
        except KeyError:
            components_updates_queue[component.key] = _comp_v
        try:
            entities_updates_queue[entity.entity_id].update(_ent_v)
        except KeyError:
            entities_updates_queue[entity.entity_id] = _ent_v

    @staticmethod
    def _batch_component_for_delete(component_delete_queue, entities_delete_queue, entity, component):
        LOGGER.core.debug('Data to delete')
        try:
            component_delete_queue[component.key].append(entity.entity_id)
        except KeyError:
            component_delete_queue[component.key] = [entity.entity_id]
        try:
            entities_delete_queue[entity.entity_id].append(component.key)
        except KeyError:
            entities_delete_queue[entity.entity_id] = [component.key]

    def _update_relative_value_for_numeric_component(self, pipeline, entity, component):
        LOGGER.core.debug('Relative value, component data incr')
        assert component.component_type == int
        pipeline.hincrby(
            '{}:{}:{}'.format(self._component_prefix, component.key, self._data_suffix),
            entity.entity_id, int(component.operation)
        )
        pipeline.hincrby(
            '{}:{}'.format(self._entity_prefix, entity.entity_id),
            component.key, int(component.operation)
        )

    @staticmethod
    def _update_boolean_component(pipeline, entity, component):
        assert component.component_type == bool
        LOGGER.core.debug('No data to set, component active')

    def _do_batch_updates(self, pipeline, entities_updates, components_updates):
        for up_en_id, _up_values_by_en in entities_updates.items():
            pipeline.hmset_dict('{}:{}'.format(self._entity_prefix, up_en_id), _up_values_by_en)

        for up_c_key, _up_values_by_comp in components_updates.items():
            pipeline.hmset_dict(
                '{}:{}:{}'.format(self._component_prefix, up_c_key, self._data_suffix),
                _up_values_by_comp
            )

    def _do_batch_deletes(self, pipeline, deletions_by_entity, deletions_by_component):
        for del_c_key, _del_entities in deletions_by_component.items():
            pipeline.hdel('{}:{}:{}'.format(self._component_prefix, del_c_key, self._data_suffix), *_del_entities)

        for _del_en_id, _del_components in deletions_by_entity.items():
            pipeline.hdel('{}:{}'.format(self._entity_prefix, _del_en_id), *_del_components)

    @staticmethod
    def _handle_index_for_struct_component(pipeline, component, k, vv, entity):
        for v in vv:
            v = v.value
            assert isinstance(v, (bool, int, str)), v
            index_type = component.get_index_type(k)
            index_key = 'i:c:{}:{}'.format(component.key, k)
            if index_type == bool:
                if v:
                    pipeline.zadd(index_key, 0, entity.entity_id)
                else:
                    pipeline.zrem(index_key, entity.entity_id)
            elif index_type == str:
                if v:
                    pipeline.zadd(index_key, 0, entity.entity_id)
                    pipeline.mantain_valued_index(component, k, v, entity.entity_id)
                else:
                    pipeline.zrem(index_key, entity.entity_id)
                    pipeline.drop_value_from_index(index_key, v, entity.entity_id)
            else:
                raise ValueError('Unknown index type: %s' % index_type)

    def _update_struct_component(self, pipeline, entity, component):
        for k, v in component.pending_changes.items():
            component.has_index(k) and self._handle_index_for_struct_component(pipeline, component, k, v, entity)
            comp_key = component.enum
            if component.get_subtype(k) == int:
                for action in v:
                    if isinstance(action, StructSubtypeIntIncrAction):
                        pipeline.hincrby('c:{}:d:{}'.format(comp_key, k), entity.entity_id, action.value)
                        pipeline.hincrby('e:{}:c:{}'.format(entity.entity_id, comp_key), k, action.value)
                    elif isinstance(action, StructSubtypeIntSetAction):
                        pipeline.hset('c:{}:d:{}'.format(comp_key, k), entity.entity_id, action.value)
                        pipeline.hset('e:{}:c:{}'.format(entity.entity_id, comp_key), k, action.value)
                    elif isinstance(action, StructSubTypeSetNull):
                        pipeline.hdel('c:{}:d:{}'.format(comp_key, k), entity.entity_id)
                        pipeline.hdel('e:{}:c:{}'.format(entity.entity_id, comp_key), k)
                    else:
                        raise ValueError('Invalid action type')
            elif component.get_subtype(k) == str:
                for action in v:
                    if isinstance(action, StructSubtypeStrSetAction):
                        pipeline.hset('c:{}:d:{}'.format(comp_key, k), entity.entity_id, action.value)
                        pipeline.hset('e:{}:c:{}'.format(entity.entity_id, comp_key), k, action.value)
                    elif isinstance(action, StructSubTypeSetNull):
                        pipeline.hdel('c:{}:d:{}'.format(comp_key, k), entity.entity_id)
                        pipeline.hdel('e:{}:c:{}'.format(entity.entity_id, comp_key), k)
                    else:
                        raise ValueError('Invalid action type')
            elif component.get_subtype(k) == list:
                for action in v:
                    if isinstance(action, StructSubtypeListAction):
                        payload = []
                        _ = [payload.extend([int(time.time()*100000), _v]) for _v in action.values]
                        if action.type == 'append':
                            pipeline.zadd('c:{}:zs:e:{}:{}'.format(comp_key, entity.entity_id, k), *payload)
                        elif action.type == 'remove':
                            pipeline.zrem('c:{}:zs:e:{}:{}'.format(comp_key, entity.entity_id, k), *action.values)
                        else:
                            raise ValueError('Invalid action type')
                    elif isinstance(action, StructSubTypeSetNull):
                        pipeline.delete('c:{}:zs:e:{}:{}'.format(comp_key, entity.entity_id, k))
                    else:
                        raise ValueError('Invalid action type')
            elif component.get_subtype(k) == bool:
                for action in v:
                    if isinstance(action, StructSubTypeBoolOff):
                        pipeline.hset('c:{}:d:{}'.format(comp_key, k), entity.entity_id, 0)
                        pipeline.hset('e:{}:c:{}'.format(entity.entity_id, comp_key), k, 0)
                    elif isinstance(action, StructSubTypeBoolOn):
                        pipeline.hset('c:{}:d:{}'.format(comp_key, k), entity.entity_id, 1)
                        pipeline.hset('e:{}:c:{}'.format(entity.entity_id, comp_key), k, 1)
                    elif isinstance(action, StructSubTypeSetNull):
                        pipeline.hdel('c:{}:d:{}'.format(comp_key, k), entity.entity_id, action.value)
                        pipeline.hdel('e:{}:c:{}'.format(entity.entity_id, comp_key), k, action.value)
                    else:
                        raise ValueError('Invalid action type')
            elif component.get_subtype(k) == dict:
                for action in v:
                    if isinstance(action, StructSubTypeDictSetKeyValueAction):
                        if isinstance(action.value, bool):
                            action.value = int(action.value)
                        pipeline.hset('c:{}:d:{}:{}'.format(comp_key, k, action.key), entity.entity_id, action.value)
                        pipeline.hset('e:{}:c:{}:{}'.format(entity.entity_id, comp_key, k), action.key, action.value)
                    elif isinstance(action, StructSubTypeDictRemoveKeyValueAction):
                        pipeline.hdel('c:{}:d:{}:{}'.format(comp_key, k, action.key), entity.entity_id)
                        pipeline.hdel('e:{}:c:{}:{}'.format(entity.entity_id, comp_key, k), action.key)
                    else:
                        raise ValueError('Invalid action type %s' % str(action))
            else:
                raise ValueError('Invalid type')
        component.pending_changes = {}

    async def update_entities(self, *entities: Entity) -> Entity:
        redis = await self.async_redis()
        pipeline = RedisLUAPipeline(redis)
        entities_updates_queue = {}
        components_updates_queue = {}
        entities_delete_queue = {}
        components_delete_queue = {}
        for entity in entities:
            assert entity.entity_id
            self._check_bounds_for_update(pipeline, entity)
        for entity in entities:
            for component in entity.pending_changes.values():
                if component.enum == ComponentTypeEnum.POS:
                    self.map_repository.update_map_position_for_entity(component, entity, pipeline)
                pipeline.setbit(
                    '{}:{}:{}'.format(self._component_prefix, component.key, self._map_suffix),
                    entity.entity_id, Bit.ON.value if component.is_active() else Bit.OFF.value
                )
                if component.is_struct:
                    self._update_struct_component(pipeline, entity, component)
                elif component.is_array():
                    self._update_array_for_entity(pipeline, entity, component)
                elif component.has_data() and component.has_value() and component.has_operation():
                    self._update_relative_value_for_numeric_component(pipeline, entity, component)
                elif not component.has_data() and component.is_active():
                    self._update_boolean_component(pipeline, entity, component)
                elif component.has_data() and not component.has_operation() and component.has_value():
                    self._batch_component_for_update(
                        components_updates_queue, entities_updates_queue, entity, component
                    )
                else:
                    self._batch_component_for_delete(components_delete_queue, entities_delete_queue, entity, component)
                LOGGER.core.debug(
                    'EntityRepository.update_entity_components. ids: %s, updates: %s, deletions: %s)',
                    entity.entity_id,
                    entities_updates_queue.get(entity.entity_id),
                    entities_delete_queue.get(entity.entity_id)
                )
        self._do_batch_updates(pipeline, entities_updates_queue, components_updates_queue)
        self._do_batch_deletes(pipeline, entities_delete_queue, components_delete_queue)
        response = await pipeline.execute()
        for entity in entities:
            entity.clear_bounds().pending_changes.clear()

        LOGGER.core.debug('EntityRepository.update_entity_components, response: %s', response)
        return response

    async def get_component_value_by_entity_id(
            self, entity_id: int, component: typing.Type[ComponentType]
    ) -> typing.Optional[ComponentType]:
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        redis = await self.async_redis()
        instance_of_value = None
        if component.component_type == bool:
            pipeline = redis.pipeline()
            pipeline.getbit('{}:{}:{}'.format(self._component_prefix, component.key, self._map_suffix), entity_id)
            res = await pipeline.execute()
            if not res:
                return
            component_value = res[0]
            if component.has_default:
                instance_of_value = res[1]
        else:
            res = await redis.hget('{}:{}'.format(self._entity_prefix, entity_id), component.key)
            if not res:
                return
            component_value = res
        if not component_value:
            if component == PosComponent:
                return
            elif not instance_of_value:
                # Todo - Remove once all the entities are fixed with a proper InstanceOf
                LOGGER.core.error('Entity id {} has not InstanceOfComponent'.format(entity_id))
                return
            return self.library_repository.get_defaults_for_library_element(instance_of_value.decode(), component)
        return res and component(component.cast_type(component_value))

    async def get_components_values_by_entities(
            self,
            entities: typing.List[Entity],
            components: typing.List[typing.Type[ComponentType]]
    ) -> typing.Dict[int, typing.Dict[ComponentTypeEnum, bytes]]:
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        for component in components:
            assert not component.is_array(), 'At the moment is not possible to use this API with array components'

        _bits_statuses = await self._get_components_statuses_by_entities(entities, components)
        _filtered = await self._get_components_values_from_entities_storage(_bits_statuses)
        return {
            e.entity_id: {
                c.enum: c.cast_type(_filtered.get(e.entity_id, {}).get(c.key)) for c in components
            } for e in entities
        }

    async def get_components_values_by_entities_ids(
            self,
            entities_ids: typing.List[int],
            components: typing.List[typing.Type[ComponentType]]
    ) -> typing.Dict[int, typing.Dict[ComponentTypeEnum, bytes]]:
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        for component in components:
            assert not (inspect.isclass(component) and issubclass(component, StructComponent))
        _bits_statuses = await self._get_components_statuses_by_entities_ids(entities_ids, components)
        _filtered = await self._get_components_values_from_entities_storage(_bits_statuses)
        return {
            entity_id: {
                c.enum: c.cast_type(_filtered.get(entity_id, {}).get(c.key)) for c in components
            } for entity_id in entities_ids
        }

    async def get_raw_component_value_by_entity_ids(
            self, component, *entity_ids: int):
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        assert not component.is_array(), 'At the moment is not possible to use this API with array components'
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for entity_id in entity_ids:
            key = '{}:{}'.format(self._entity_prefix, entity_id)
            pipeline.hmget(key, component.key)
        results = await pipeline.execute()
        response = []
        for result in results:
            if result[1]:
                response.append(result[1] and result[1].decode())
        return response

    async def get_components_values_by_components_storage(
            self,
            entity_ids: typing.List[int],
            components: typing.List[typing.Type[ComponentType]]
    ) -> typing.Dict[ComponentTypeEnum, typing.Dict[int, bytes]]:
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
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
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
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

    async def _get_components_statuses_by_entities_ids(
            self,
            entities_ids: typing.List[int],
            components: typing.List[typing.Type[ComponentType]]
    ) -> OrderedDict:
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        bits_by_entity = OrderedDict()
        for _e in entities_ids:
            for _c in components:
                key = '{}:{}:{}'.format(self._component_prefix, _c.key, self._map_suffix)
                pipeline.getbit(key, _e)
        data = await pipeline.execute()
        i = 0
        for ent in entities_ids:
            for comp in components:
                _ent_v = {comp.key: [data[i], comp.component_type != bool]}
                try:
                    bits_by_entity[ent].update(_ent_v)
                except KeyError:
                    bits_by_entity[ent] = _ent_v
                i += 1
        return bits_by_entity

    async def _get_components_statuses_by_components(
            self,
            entities: typing.List[int],
            components: typing.List[typing.Type[ComponentType]]
    ) -> OrderedDict:
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
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
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
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
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for c_key in filtered_query:
            entity_ids = [
                ent_id for ent_id, status_and_querable in filtered_query[c_key].items()
                if all(status_and_querable)
            ]
            if entity_ids:
                for eid in entity_ids:
                    pipeline.hget('c:{}:d:{}'.format(SystemComponent.key, 'instance_of'), eid)
                comp = get_component_by_enum_value(c_key)
                if comp.is_array():
                    for eid in entity_ids:
                        pipeline.zrange(
                            '{}:{}:{}:{}'.format(self._component_prefix, c_key, self._zset_suffix, eid),
                            0,
                            -1
                        )
                else:
                    pipeline.hmget(
                        '{}:{}:{}'.format(self._component_prefix, c_key, self._data_suffix),
                        *entity_ids
                    )
        entities_instance_of = []
        response = []
        arrays = {}
        redis_response = await pipeline.execute()
        i = 0
        for c_key in filtered_query:
            entity_ids = [
                ent_id for ent_id, status_and_querable in filtered_query[c_key].items()
                if all(status_and_querable)
            ]
            if entity_ids:
                for _ in entity_ids:
                    entities_instance_of.append(redis_response[i])
                    i += 1
                comp = get_component_by_enum_value(c_key)
                if comp.is_array():
                    for eid in entity_ids:
                        arrays['{}.{}'.format(eid, c_key)] = redis_response[i]
                        i += 1
                else:
                    response.append(redis_response[i])
                    i += 1
            else:
                response.append(None)
        data = {}
        i = 0
        for c_key, values in filtered_query.items():
            e_i = 0
            for entity_id, status in values.items():
                component = get_component_by_enum_value(ComponentTypeEnum(c_key))
                if not status[1]:
                    if component.has_default:
                        value = status[0] or self.library_repository.get_defaults_for_library_element(
                            entities_instance_of[e_i].decode(),
                            component.libname
                        )
                        value = value.value if (not status[0] and value) else value
                    else:
                        value = status[0]
                    try:
                        data[ComponentTypeEnum(c_key)].update({entity_id: value})
                    except KeyError:
                        data[ComponentTypeEnum(c_key)] = {entity_id: value}
                elif all(status):
                    if component.is_array():
                        if component.has_default:
                            value = arrays['{}.{}'.format(e_i, component.key)]
                            value = value or self.library_repository.get_defaults_for_library_element(
                                        entities_instance_of[e_i].decode(),
                                        get_component_alias_by_enum_value(ComponentTypeEnum(c_key))
                                    ).value
                        else:
                            value = arrays['{}.{}'.format(entity_id, component.key)]
                    else:
                        if component.has_default:
                            value = response[i][e_i] or self.library_repository.get_defaults_for_library_element(
                                entities_instance_of[e_i].decode(),
                                get_component_alias_by_enum_value(ComponentTypeEnum(c_key))
                            )
                            value = value.value if (not response[i][e_i] and value) else value
                        else:
                            value = response[i][e_i]
                    try:
                        data[ComponentTypeEnum(c_key)].update({entity_id: value})
                    except KeyError:
                        data[ComponentTypeEnum(c_key)] = {entity_id: value}
                    except IndexError:
                        raise
                else:
                    value = self.library_repository.get_defaults_for_library_element(
                        entities_instance_of[e_i].decode(),
                        component.libname
                    ) if component.has_default else None
                    try:
                        data[ComponentTypeEnum(c_key)].update({entity_id: value})
                    except KeyError:
                        data[ComponentTypeEnum(c_key)] = {entity_id: value}
                e_i += 1
            i += 1
        return data

    async def _get_components_values_from_entities_storage(self, filtered_query: OrderedDict):
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        components = {}
        for entity_id, v in filtered_query.items():
            for comp_key, status_and_querable in v.items():
                components[comp_key] = components.get(comp_key, get_component_by_enum_value(comp_key))
                if components[comp_key].is_array() and all(status_and_querable):
                    key = '{}:{}:{}:{}'.format(
                        self._component_prefix, comp_key, self._zset_suffix, entity_id
                    )
                    pipeline.zscan(key, 0, -1)
                elif all(status_and_querable):
                    keys = [
                        comp_key for comp_key, status_and_querable in v.items() if all(status_and_querable)
                    ]
                    pipeline.hmget('{}:{}'.format(self._entity_prefix, entity_id), *keys)
                elif not status_and_querable[1]:
                    pass
                else:
                    print(components[comp_key])
        response = await pipeline.execute()
        data = {}
        i = 0
        for entity_id, vv in filtered_query.items():
            c_i = 0
            for c_key, status_and_querable in vv.items():
                component = get_component_by_enum_value(ComponentTypeEnum(c_key))
                if component.is_array() and all(status_and_querable):
                    try:
                        data[entity_id].update({ComponentTypeEnum(c_key): response[i][1]})
                    except KeyError:
                        data[entity_id] = {ComponentTypeEnum(c_key): response[i][1]}
                elif not status_and_querable[1]:
                    if component.has_default:
                        libname = (await redis.hget(
                            'c:{}:d:{}'.format(SystemComponent.key, 'instance_of'), entity_id
                        )).decode()
                        vvv = self.library_repository.get_defaults_for_library_element(
                            libname, get_component_by_enum_value(ComponentTypeEnum(c_key))
                        )
                    else:
                        vvv = None
                    try:
                        data[entity_id].update({ComponentTypeEnum(c_key): vvv})
                    except KeyError:
                        data[entity_id] = {ComponentTypeEnum(c_key): vvv}
                elif all(status_and_querable):
                    if component.has_default:
                        if not response[i][c_i]:
                            libname = (await redis.hget(
                                'c:{}:d:{}'.format(SystemComponent.key, 'instance_of'), entity_id
                            )).decode()
                        else:
                            libname = ""
                        value = response[i][c_i] or self.library_repository.get_defaults_for_library_element(
                            libname, get_component_by_enum_value(ComponentTypeEnum(c_key))
                        )
                        value = value.value if (not response[i][c_i] and value) else value
                    else:
                        value = response[i][c_i]
                    try:
                        data[entity_id].update({ComponentTypeEnum(c_key): value})
                    except KeyError:
                        data[entity_id] = {ComponentTypeEnum(c_key): value}
                    i += 1
                    c_i += 1
                else:
                    assert not component.has_default
                    try:
                        data[entity_id].update({ComponentTypeEnum(c_key): None})
                    except KeyError:
                        data[entity_id] = {ComponentTypeEnum(c_key): None}
        return data

    async def populate_area_content_for_area(self, entity: Entity, area: Area) -> None:
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        # TODO FIXME
        for _room in area.rooms:
            if _room:
                for _entity_id in _room.entity_ids:
                    _room.add_entity(Entity(_entity_id))

    async def delete_entity(self, entity_id: int):
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
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

    async def filter_entities_with_active_component(self, component, *entities):
        """
        USE OLD STYLE COMPONENTS, GOING TO BE DEPRECATED.
        """
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        for entity in entities:
            pipeline.getbit(
                '{}:{}:{}'.format(self._component_prefix, component.key, self._map_suffix),
                int(entity)
            )
        result = await pipeline.execute()
        return [int(entities[i]) for i, v in enumerate(result) if v]

    ###################################################
    # BEGIN STRUCT COMPONENTS (COMPONENTS 2.0) SUPPORT #
    # BEGIN STRUCT COMPONENTS (COMPONENTS 2.0) SUPPORT #
    # BEGIN STRUCT COMPONENTS (COMPONENTS 2.0) SUPPORT #
    # BEGIN STRUCT COMPONENTS (COMPONENTS 2.0) SUPPORT #
    # BEGIN STRUCT COMPONENTS (COMPONENTS 2.0) SUPPORT #
    # BEGIN STRUCT COMPONENTS (COMPONENTS 2.0) SUPPORT #
    ###################################################

    @staticmethod
    def _enqueue_full_struct_component_read_for_entity(primitives, pipeline, component, entity_id):
        for meta in component.meta:
            subkey, subtype = meta
            if subtype in (str, int, bool):
                if not primitives.get(component):
                    primitives[component] = []
                primitives[component].append(subkey)
            elif subtype == dict:
                pipeline.hgetall('e:{}:c:{}:{}'.format(entity_id, component.key, subkey))
            elif subtype == list:
                pipeline.zrange('c:{}:zs:e:{}:{}'.format(component.key, entity_id, subkey), 0, -1)
            else:
                raise ValueError('Unknown type')

    @staticmethod
    def _enqueue_selective_struct_component_read_for_entity(primitives, pipeline, component_query, entity_id):
        component = component_query[0]
        keys = component_query[1:]
        for key in keys:
            if component.get_subtype(key) in (str, int, bool):
                if not primitives.get(component):
                    primitives[component] = []
                primitives[component].append(key)
            elif component.get_subtype(key) == dict:
                pipeline.hgetall('e:{}:c:{}:{}'.format(entity_id, component.key, key))
            elif component.get_subtype(key) == list:
                pipeline.zrange('c:{}:zs:e:{}:{}'.format(component.key, entity_id, key), 0, -1)
            else:
                raise ValueError('Unknown type: %s' % key)

    def _resolve_full_struct_component_read_for_entity(
            self, redis_response, response, component, pos: typing.List[int], entity_type: typing.Optional[str]
    ):
        if not response.get(component.enum):
            response[component.enum] = component()
        for meta in component.meta:
            subkey, subtype = meta
            if subtype in (str, int, bool):
                pass
            elif subtype == dict:
                value = self._load_value_or_default(component, subkey, redis_response[pos[0]], entity_type)
                load_value_in_struct_component(response[component.enum], subkey, value)
                pos[0] += 1
            elif subtype == list:
                value = self._load_value_or_default(component, subkey, redis_response[pos[0]], entity_type)
                load_value_in_struct_component(response[component.enum], subkey, value)
                pos[0] += 1
            else:
                raise ValueError('Unknown type')

    def _resolve_selective_struct_component_read_for_entity(
            self, redis_response, response, component_query, pos: typing.List[int], entity_type: typing.Optional[str]
    ):
        component = component_query[0]
        keys = component_query[1:]
        for key in keys:
            if component.get_subtype(key) in (str, int, bool):
                pass
            elif component.get_subtype(key) == dict:
                if not response.get(component.enum):
                    response[component.enum] = component()
                value = self._load_value_or_default(component, key, redis_response[pos[0]], entity_type)
                load_value_in_struct_component(response[component.enum], key, value)
                pos[0] += 1
            elif component.get_subtype(key) == list:
                if not response.get(component.enum):
                    response[component.enum] = component()
                value = self._load_value_or_default(component, key, redis_response[pos[0]], entity_type)
                load_value_in_struct_component(response[component.enum], key, value)
                pos[0] += 1
            else:
                raise ValueError('Unknown type %s' % key)

    @staticmethod
    def _enqueue_gather_entity_types_for_defaults(pipeline, entity_ids, components) -> bool:
        has_defaults = False
        for comp in components:
            if isinstance(comp, (tuple, list)):
                if comp[1] in comp[0].defaults:
                    has_defaults = True
                    break
            elif inspect.isclass(comp) and issubclass(comp, StructComponent):
                if comp.defaults:
                    has_defaults = True
                    break
            else:
                raise ValueError('Unknown type')
        if has_defaults:
            key = 'c:{}:d:{}'.format(SystemComponent.key, 'instance_of')
            pipeline.hmget(key, *entity_ids)
        return has_defaults

    @staticmethod
    def _resolve_gather_entity_types_for_defaults(redis_result, entity_ids, pos) -> typing.Dict:
        pos[0] += 1
        return {
            entity_ids[i]: v.decode() for i, v in enumerate(redis_result[0])
        }

    async def read_struct_components_for_entity(
            self,
            entity_id,
            *components: typing.Union[typing.Type[StructComponent], typing.Union[tuple, list]]
    ):
        """
        This is tailored on the DB to read from the same entity table.
        """
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        primitives = {}
        components_has_defaults = self._enqueue_gather_entity_types_for_defaults(pipeline, [entity_id], components)
        for component in components:
            if isinstance(component, (tuple, list)):
                self._enqueue_selective_struct_component_read_for_entity(primitives, pipeline, component, entity_id)
            elif issubclass(component, StructComponent):
                self._enqueue_full_struct_component_read_for_entity(primitives, pipeline, component, entity_id)
            else:
                raise ValueError('Unknown type')
        for comp, v in primitives.items():
            pipeline.hmget('e:{}:c:{}'.format(entity_id, comp.key), *v)
        result = await pipeline.execute()
        response = dict()
        i = [0]
        if components_has_defaults:
            entity_types = self._resolve_gather_entity_types_for_defaults(result, [entity_id], i)
            entity_type = entity_types and entity_types[entity_id] or None
        else:
            entity_type = None
        for component in components:
            if isinstance(component, (tuple, list)):
                self._resolve_selective_struct_component_read_for_entity(
                    primitives, pipeline, component, i, entity_type
                )
            elif issubclass(component, StructComponent):
                self._resolve_full_struct_component_read_for_entity(
                    result, response, component, i, entity_type
                )
            else:
                raise ValueError('Unknown type')
        for component, keys in primitives.items():
            if not response.get(component.enum):
                response[component.enum] = component()
            ki = 0
            for key in keys:
                value = self._load_value_or_default(component, key, result[i[0]][ki], entity_type)
                load_value_in_struct_component(response[component.enum], key, value)
                ki += 1
            i[0] += 1
        return response

    async def get_entity_ids_with_valued_components(
        self,
        *components: typing.Tuple[StructComponent, str]
    ):
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        entity_ids = []
        for component in components:
            for component_column in component[1:]:
                index_key = 'i:c:{}:{}'.format(component[0].key, component_column)
                pipeline.zrange(index_key, 0, -1)
        res = await pipeline.execute()
        _ = [entity_ids.extend((int(eid) for eid in r)) for r in res]
        return entity_ids

    async def get_entity_ids_with_components_having_value(
        self,
        *components: typing.Tuple[StructComponent, str, str]
    ):
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        entity_ids = []
        for component in components:
            index_key = 'i:c:{}:{}:{}'.format(component[0].key, component[1], component[2])
            pipeline.zrange(index_key, 0, -1)
        res = await pipeline.execute()
        _ = [entity_ids.extend((int(eid) for eid in r)) for r in res]
        return entity_ids

    async def read_struct_components_for_entities(
        self,
        entity_ids: typing.List[int],
        *components: typing.Type[typing.Union[tuple, list, StructComponent]]
    ):
        """
        This is more effective to mount the same components on multiple entities.
        """
        redis = await self.async_redis()
        pipeline = redis.pipeline()
        components_has_defaults = self._enqueue_gather_entity_types_for_defaults(pipeline, entity_ids, components)
        for component in components:
            if isinstance(component, (tuple, list)):
                self._enqueue_selective_struct_component_read_multiple_entities(pipeline, entity_ids, component)
            elif inspect.isclass(component) and issubclass(component, StructComponent):
                self._enqueue_full_struct_component_read_multiple_entities(pipeline, entity_ids, component)
            else:
                raise ValueError('Unknown type: %s' % component)
        redis_response = await pipeline.execute()
        response = {entity_id: {} for entity_id in entity_ids}
        pos = [0]
        if components_has_defaults:
            entity_types = self._resolve_gather_entity_types_for_defaults(redis_response, entity_ids, pos)
        else:
            entity_types = {}
        for component in components:
            if isinstance(component, (tuple, list)):
                self._resolve_selective_struct_component_read_multiple_entities(
                    redis_response, response, entity_ids, component, pos, entity_types
                )
            elif issubclass(component, StructComponent):
                self._resolve_full_struct_component_read_multiple_entities(
                    redis_response, response, entity_ids, component, pos, entity_types
                )
        return response

    @staticmethod
    def _enqueue_selective_struct_component_read_multiple_entities(
            pipeline, entity_ids, component_query: (tuple, list)
    ):
        component = component_query[0]
        keys = component_query[1:]
        for key in keys:
            if component.get_subtype(key) in (str, bool, int):
                pipeline.hmget('c:{}:d:{}'.format(component.key, key), *entity_ids)
            elif component.get_subtype(key) == list:
                for entity_id in entity_ids:
                    pipeline.zrange('c:{}:zs:e:{}:{}'.format(component.key, entity_id, key), 0, -1)
            elif component.get_subtype(key) == dict:
                for entity_id in entity_ids:
                    pipeline.hgetall('e:{}:c:{}:{}'.format(entity_id, component.key, key))
            else:
                raise ValueError('Unknown subtype {}.{}'.format(component, key))

    def _resolve_selective_struct_component_read_multiple_entities(
            self, redis_response, response, entity_ids, component_query: (tuple, list), pos, entity_types
    ):
        component = component_query[0]
        keys = component_query[1:]
        assert keys
        for key in keys:
            if component.get_subtype(key) in (str, bool, int):
                data = redis_response[pos[0]]
                for i, entity_id in enumerate(entity_ids):
                    if not response[entity_id].get(component.enum):
                        response[entity_id][component.enum] = component()
                    value = self._load_value_or_default(component, key, data[i], entity_types.get(entity_id))
                    load_value_in_struct_component(response[entity_id][component.enum], key, value)
                pos[0] += 1
            elif component.get_subtype(key) == list:
                for entity_id in entity_ids:
                    data = redis_response[pos[0]]
                    if not response[entity_id].get(component.enum):
                        response[entity_id][component.enum] = component()

                    value = self._load_value_or_default(component, key, data, entity_types.get(entity_id))
                    load_value_in_struct_component(response[entity_id][component.enum], key, value)
                    pos[0] += 1
            elif component.get_subtype(key) == dict:
                for entity_id in entity_ids:
                    data = redis_response[pos[0]]
                    if not response[entity_id].get(component.enum):
                        response[entity_id][component.enum] = component()
                    value = self._load_value_or_default(component, key, data, entity_types.get(entity_id))
                    load_value_in_struct_component(response[entity_id][component.enum], key, value)
                    pos[0] += 1
            else:
                raise ValueError('Unknown subtype {}.{}'.format(component, key))

    @staticmethod
    def _enqueue_full_struct_component_read_multiple_entities(pipeline, entity_ids, component):
        for meta in component.meta:
            subkey, subtype = meta
            if subtype in (bool, str, int):
                pipeline.hmget('c:{}:d:{}'.format(component.key, subkey), *entity_ids)
            elif subtype is list:
                for entity_id in entity_ids:
                    pipeline.zrange('c:{}:zs:e:{}:{}'.format(component.key, entity_id, subkey), 0, -1)
            elif subtype is dict:
                for entity_id in entity_ids:
                    pipeline.hgetall('e:{}:c:{}:{}'.format(entity_id, component.key, subkey))
            else:
                raise ValueError

    def _resolve_full_struct_component_read_multiple_entities(
            self, redis_response, response, entity_ids, component, pos, entity_types
    ):
        for meta in component.meta:
            subkey, subtype = meta
            if subtype in (bool, str, int):
                data = redis_response[pos[0]]
                for i, entity_id in enumerate(entity_ids):
                    if not response[entity_id].get(component.enum):
                        response[entity_id][component.enum] = component()
                    value = self._load_value_or_default(component, subkey, data[i], entity_types.get(entity_id))
                    load_value_in_struct_component(response[entity_id][component.enum], subkey, value)
                pos[0] += 1
            elif subtype is list:
                for entity_id in entity_ids:
                    data = redis_response[pos[0]]
                    if not response[entity_id].get(component.enum):
                        response[entity_id][component.enum] = component()
                    value = self._load_value_or_default(component, subkey, data, entity_types.get(entity_id))
                    load_value_in_struct_component(response[entity_id][component.enum], subkey, value)
                    pos[0] += 1
            elif subtype is dict:
                for entity_id in entity_ids:
                    data = redis_response[pos[0]]
                    if not response[entity_id].get(component.enum):
                        response[entity_id][component.enum] = component()
                    value = self._load_value_or_default(component, subkey, data, entity_types.get(entity_id))
                    load_value_in_struct_component(response[entity_id][component.enum], subkey, value)
                    pos[0] += 1
            else:
                raise ValueError

    def _load_value_or_default(self, component, key, value, entity_type):
        if value:
            return value
        if key not in component.defaults:
            return value
        assert entity_type
        v = self.library_repository.get_default_value_for_struct_subkey(entity_type, component.libname, key)
        return v
