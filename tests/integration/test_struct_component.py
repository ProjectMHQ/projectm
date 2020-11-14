import asyncio
from unittest import TestCase
from unittest.mock import Mock

from core.src.world.components.base import ComponentTypeEnum
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

    def test2(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_stuff_struct_component())
        self.assertTrue(self.test_success)

    def test3(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._test_selective_repo_queries())
        self.assertTrue(self.test_success)

    async def _test_save_struct_component(self):
        entity = Entity(555)
        entity2 = Entity(556)

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
            .manystuffhere.append(3, 6, 9)\
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
        self.assertEqual(component.manystuffhere, [3, 6, 9])
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
        self.assertEqual(component.a, {'key2': 'value2', 'key3': 'value3'})
        self.assertEqual(component.manystuffhere, [3, 6, 9])
        self.assertEqual(component.integerrr, 42)
        self.assertEqual(component.boolean, True)
        c.weirdstuff.null()
        entity.set_for_update(c)
        await self.sut.update_entities(entity)
        res = await self.sut.read_struct_components_for_entities([555], TestComponent)
        component = res[555][0]
        self.assertEqual(component.weirdstuff, None)
        self.assertEqual(component.manystuffhere, [3, 6, 9])
        self.assertEqual(component.integerrr, 42)
        self.assertEqual(component.boolean, True)
        c.manystuffhere.remove(3)
        c.weirdstuff.set('yahi!')
        entity.set_for_update(c)
        await self.sut.update_entities(entity)
        res = await self.sut.read_struct_components_for_entities([555], TestComponent)
        component = res[555][0]
        self.assertEqual(component.weirdstuff, 'yahi!')
        self.assertEqual(component.manystuffhere, [6, 9])
        c.manystuffhere.remove(6, 9)
        entity.set_for_update(c)
        c2 = TestComponent().manystuffhere.append(666)
        entity2.set_for_update(c2)
        await self.sut.update_entities(entity, entity2)
        res = await self.sut.read_struct_components_for_entities([555, 556], TestComponent)
        component = res[555][0]
        component2 = res[556][0]
        self.assertEqual(component.manystuffhere, [])
        self.assertEqual(component2.manystuffhere, [666])
        self.assertEqual(component2.manystuffhere + [2], [666, 2])
        self.test_success = True

    async def _test_stuff_struct_component(self):
        class TestComponent2(StructComponent):
            enum = ComponentTypeEnum.SYSTEM
            meta = (
                ('weirdstuff', str),
                ('manystuffhere', list),
                ('integerrr', int),
                ('boolean', bool),
                ('a', dict)
            )

        class TestComponent(StructComponent):
            enum = ComponentTypeEnum.INVENTORY
            meta = (
                ('weirdstuff', str),
                ('manystuffhere', list),
                ('integerrr', int),
                ('boolean', bool),
                ('a', dict)
            )
            indexes = ('weirdstuff', )

        ent = Entity(444)
        c3 = TestComponent().weirdstuff.set('weirdstuff').a.set('key', 'value').manystuffhere.append(3)
        c4 = TestComponent2().weirdstuff.set('weirdstuff2').a.set('key', 'value2').manystuffhere.append(6)
        ent.set_for_update(c3).set_for_update(c4)
        await self.sut.update_entities(ent)
        res = await self.sut.read_struct_components_for_entity(444, TestComponent, TestComponent2)
        self.assertEqual(res[c3.enum].weirdstuff, 'weirdstuff')
        self.assertEqual(res[c3.enum].a, {'key': 'value'})
        self.assertEqual(res[c4.enum].weirdstuff, 'weirdstuff2')
        self.assertEqual(res[c4.enum].a, {'key': 'value2'})

        self.test_success = True

    async def _test_selective_repo_queries(self):

        class TestComponent(StructComponent):
            enum = 1
            key = enum
            meta = (
                ('weirdstuff', str),
                ('manystuffhere', list),
                ('integerrr', int),
                ('boolean', bool),
                ('a', dict)
            )

        c = TestComponent().weirdstuff.set('weirdstuff').a.set('key', 'value').manystuffhere.append(3)
        entity = Entity(123)
        entity.set_for_update(c)
        await self.sut.update_entities(entity)
        res = await self.sut.read_struct_components_for_entities([123], (TestComponent, 'weirdstuff'))
        r = res[123][c.enum]
        self.assertEqual(r.weirdstuff, 'weirdstuff')
        self.assertEqual(r.manystuffhere, [])
        self.assertEqual(r.integerrr, 0)
        self.assertEqual(r.boolean, False)
        self.assertEqual(r.a, {})
        self.test_success = True
