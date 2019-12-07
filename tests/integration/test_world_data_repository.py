import asyncio
from unittest import TestCase
from core.src.world.components import ComponentTypeEnum
from core.src.world.components.character import CharacterComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.name import NameComponent
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity, EntityID
from core.src.world.repositories.data_repository import RedisDataRepository
from core.src.world.services.system_utils import get_redis_factory, RedisType
from etc import settings


class TestWorldDataRepository(TestCase):
    def setUp(self):
        assert settings.INTEGRATION_TESTS
        assert settings.RUNNING_TESTS
        asyncio.get_event_loop().run_until_complete(self._flush_redis())

        self.sut = RedisDataRepository(get_redis_factory(RedisType.DATA))
        self.test_success = False

    async def _flush_redis(self):
        r = get_redis_factory(RedisType.DATA)
        await (await r()).flushdb()

    async def redis(self):
        return await self.sut.async_redis()

    def tearDown(self):
        self.sut = RedisDataRepository(self.redis)

    def test(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.test_get_set())
        self.assertTrue(self.test_success)

    async def test_get_set(self):
        redis = await self.redis()
        _entity_name = 'Billy Zinna'
        entity = Entity()
        entity.set(NameComponent(_entity_name))

        data = await redis.hget('c:2:d', 1)
        self.assertIsNone(data)
        self.assertEqual(await redis.getbit('c:2:m', 1), 0)
        self.assertEqual(await redis.getbit('c:5:m', 1), 0)

        await self.sut.save_entity(entity)
        self.assertEqual(await redis.getbit('c:5:m', 1), 0)
        self.assertEqual(await redis.getbit('c:3:m', 1), 0)
        name_on_component_storage = await redis.hget('c:2:d', 1)
        self.assertEqual(name_on_component_storage, _entity_name.encode())
        name_on_entity_storage = await redis.hget('e:1', 2)
        self.assertEqual(name_on_entity_storage, _entity_name.encode())

        response = await self.sut.get_components_values_by_entities(
            [entity], [NameComponent, CharacterComponent, ConnectionComponent]
        )
        self.assertEqual(
            {
                EntityID(1): {
                    ComponentTypeEnum.NAME: 'Billy Zinna',
                    ComponentTypeEnum.CHARACTER: False,
                    ComponentTypeEnum.CONNECTION: None
                }
            },
            response
        )
        response_by_components = await self.sut.get_components_values_by_components(
            [entity.entity_id], [NameComponent, CharacterComponent, ConnectionComponent]
        )
        self.assertEqual(
            {
                ComponentTypeEnum.NAME: {
                    EntityID(1): 'Billy Zinna'
                },
                ComponentTypeEnum.CHARACTER: {
                    EntityID(1): False
                },
                ComponentTypeEnum.CONNECTION: {
                    EntityID(1): None
                }
            },
            response_by_components
        )
        entity.set(CharacterComponent(True))
        await self.sut.update_entities(entity)
        self.assertTrue(await redis.getbit('c:5:m', 1))
        self.assertIsNone(await redis.hget('c:5:d', 1))
        response = await self.sut.get_components_values_by_entities([entity], [CharacterComponent])

        self.assertEqual(
            {
                EntityID(1): {
                    ComponentTypeEnum.CHARACTER: True,
                }
            },
            response
        )
        response = await self.sut.get_components_values_by_entities(
            [entity],
            [CharacterComponent, NameComponent, PosComponent]
        )
        response_by_components = await self.sut.get_components_values_by_components(
            [entity.entity_id], [NameComponent, CharacterComponent, ConnectionComponent]
        )
        self.assertEqual(
            {
                ComponentTypeEnum.NAME: {
                    EntityID(1): 'Billy Zinna'
                },
                ComponentTypeEnum.CHARACTER: {
                    EntityID(1): True
                },
                ComponentTypeEnum.CONNECTION: {
                    EntityID(1): None
                }
            },
            response_by_components
        )
        self.assertEqual(
            {
                EntityID(1): {
                    ComponentTypeEnum.NAME: 'Billy Zinna',
                    ComponentTypeEnum.CHARACTER: True,
                    ComponentTypeEnum.POS: None
                }
            },
            response
        )
        await self.sut.update_entities(entity.set(CharacterComponent(False)))
        response = await self.sut.get_components_values_by_entities([entity], [CharacterComponent])

        self.assertEqual(
            {
                EntityID(1): {
                    ComponentTypeEnum.CHARACTER: False,
                }
            },
            response
        )
        response_by_components = await self.sut.get_components_values_by_components(
            [entity.entity_id], [CharacterComponent]
        )
        self.assertEqual(
            {
                ComponentTypeEnum.CHARACTER: {
                    EntityID(1): False
                },
            },
            response_by_components
        )
        """
        second entity starts here
        """
        _entity_2_name = 'Donna Arcama'
        entity_2 = Entity()
        entity_2.set(NameComponent(_entity_2_name))
        await self.sut.save_entity(entity_2)
        await self.sut.update_entities(entity.set(CharacterComponent(True)), entity_2)
        response = await self.sut.get_components_values_by_entities(
            [entity, entity_2],
            [CharacterComponent, NameComponent, PosComponent]
        )
        response_by_components = await self.sut.get_components_values_by_components(
            [entity.entity_id, entity_2.entity_id],
            [NameComponent, CharacterComponent, ConnectionComponent]
        )
        self.assertEqual(
            {
                ComponentTypeEnum.NAME: {
                    EntityID(1): 'Billy Zinna',
                    EntityID(2): 'Donna Arcama'
                },
                ComponentTypeEnum.CHARACTER: {
                    EntityID(1): True,
                    EntityID(2): False
                },
                ComponentTypeEnum.CONNECTION: {
                    EntityID(1): None,
                    EntityID(2): None
                }
            },
            response_by_components
        )
        self.assertEqual(
            {
                EntityID(1): {
                    ComponentTypeEnum.NAME: 'Billy Zinna',
                    ComponentTypeEnum.CHARACTER: True,
                    ComponentTypeEnum.POS: None
                },
                EntityID(2): {
                    ComponentTypeEnum.NAME: 'Donna Arcama',
                    ComponentTypeEnum.CHARACTER: False,
                    ComponentTypeEnum.POS: None
                }
            },
            response
        )
        self.test_success = True
