import asyncio
from unittest import TestCase
from unittest.mock import Mock

from core.src.world.components.base.structcomponent import StructComponent
from core.src.world.domain.entity import Entity
from core.src.world.repositories.data_repository import RedisDataRepository
from core.src.world.services.system_utils import get_redis_factory, RedisType
from etc import settings


class TestStructComponent(TestCase):
    def setUp(self):
        assert settings.INTEGRATION_TESTS
        assert settings.RUNNING_TESTS
        asyncio.get_event_loop().run_until_complete(self._flush_redis())
        self.lib_repo = Mock()
        self.map_repo = Mock()
        self.sut = RedisDataRepository(get_redis_factory(RedisType.DATA), self.lib_repo, self.map_repo)
        self.test_success = False

    async def _flush_redis(self):
        r = get_redis_factory(RedisType.DATA)
        await (await r()).flushdb()

    async def redis(self):
        return await self.sut.async_redis()

    def tearDown(self):
        self.lib_repo.reset_mock()
        self.map_repo.reset_mock()
        self.sut = RedisDataRepository(self.redis, self.lib_repo, self.map_repo)

    def test(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_save_struct_component())
        self.assertTrue(self.test_success)

    async def _test_save_struct_component(self):
        entity = Entity(555)

        class TestComponent(StructComponent):
            component_enum = 0
            meta = (
                ('weirdstuff', str),
                ('manystuffhere', list),
                ('integerrr', int),
                ('boolean', bool),
                ('a', dict)
            )

        c = TestComponent()\
            .weirdstuff.set('a lot of')\
            .manystuffhere.append(3)\
            .integerrr.incr(42)\
            .boolean.set(True)\
            .a.set('key1', 'value1')\
            .a.set('key2', 'value2')\
            .a.set('key3', 'value3')
        entity.set_for_update(c)
        await self.sut.update_entities(entity)
        res = await self.sut.read_struct_components_for_entities([555], TestComponent)
        component = res[555][0]
        self.assertEqual(component.weirdstuff, 'a lot of')
        self.assertEqual(component.manystuffhere, [3])
        self.assertEqual(component.integerrr, 42)
        self.assertEqual(component.boolean, True)
        self.assertEqual(component.a['key1'], 'value1')
        self.assertEqual(component.a['key2'], 'value2')
        self.assertEqual(component.a['key3'], 'value3')
        c.a.remove('key1')
        entity.set_for_update(c)
        await self.sut.update_entities(entity)
        res = await self.sut.read_struct_components_for_entities([555], TestComponent)
        component = res[555][0]
        self.assertEqual(component.a.get('key1'), None)
        self.assertFalse(component.a.has_key('key1'))
        self.assertEqual(component.manystuffhere, [3])
        self.assertEqual(component.integerrr, 42)
        self.assertEqual(component.boolean, True)
        c.weirdstuff.null()
        entity.set_for_update(c)
        await self.sut.update_entities(entity)
        res = await self.sut.read_struct_components_for_entities([555], TestComponent)
        component = res[555][0]
        self.assertEqual(component.weirdstuff, None)
        self.assertEqual(component.manystuffhere, [3])
        self.assertEqual(component.integerrr, 42)
        self.assertEqual(component.boolean, True)
        self.test_success = True
        c.manystuffhere.remove(3)
        c.weirdstuff.set('yahi!')
        entity.set_for_update(c)
        await self.sut.update_entities(entity)
        res = await self.sut.read_struct_components_for_entities([555], TestComponent)
        component = res[555][0]
        self.assertEqual(component.weirdstuff, 'yahi!')
        self.assertEqual(component.manystuffhere, [])
