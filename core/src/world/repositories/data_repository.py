import asyncio
import inspect
import time
import typing
import aioredis
from core.src.auth.logging_factory import LOGGER
from core.src.world.components.base.structcomponent import StructSubtypeListAction, StructSubtypeStrSetAction, \
    StructSubtypeIntIncrAction, StructSubtypeIntSetAction, StructSubTypeSetNull, StructSubTypeBoolOn, \
    StructSubTypeBoolOff, StructSubTypeDictSetKeyValueAction, \
    StructSubTypeDictRemoveKeyValueAction, StructComponent, load_value_in_struct_component
from core.src.world.components.system import SystemComponent
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
        self.async_lock = asyncio.Lock()
        self._async_redis = None

    async def async_redis(self) -> aioredis.Redis:
        await self.async_lock.acquire()
        try:
            if not self._async_redis:
                self._async_redis = await self._async_redis_factory()
                await (await self._async_redis).setbit('e:m', 0, 1)  # ensure the map is 1 based
        finally:
            self.async_lock.release()
        return self._async_redis

    async def _allocate_entity_id(self) -> int:
        script = """
            local val = redis.call('bitpos', 'e:m', 0)
            redis.call('setbit', 'e:m', val, 1)
            return val
            """
        redis = await self.async_redis()
        response = await redis.eval(script, ['e:m'])
        LOGGER.core.debug('EntityRepository.create_entity, response: %s', response)
        assert response
        return int(response)

    async def entity_exists(self, entity_id):
        redis = await self.async_redis()
        return bool(await redis.keys('e:{}'.format(entity_id)))

    async def save_entity(self, entity: Entity) -> Entity:
        assert not entity.entity_id, 'entity_id: %s, use update, not save.' % entity.entity_id
        entity_id = await self._allocate_entity_id()
        entity.entity_id = entity_id
        await self.update_entities(entity)
        return entity

    @staticmethod
    def _check_bounds_for_update(pipeline: RedisLUAPipeline, entity: Entity):
        for bound in entity.bounds():
            assert bound.is_struct
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
        for entity in entities:
            assert entity.entity_id
            self._check_bounds_for_update(pipeline, entity)
        for entity in entities:
            for component in entity.pending_changes.values():
                pipeline.setbit(
                    'c:{}:m'.format(component.key),
                    entity.entity_id, Bit.ON.value if component.is_active() else Bit.OFF.value
                )
                assert component.is_struct
                self._update_struct_component(pipeline, entity, component)
        response = await pipeline.execute()
        for entity in entities:
            entity.clear_bounds().pending_changes.clear()
        LOGGER.core.debug('EntityRepository.update_entity_components, response: %s', response)
        return response

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
