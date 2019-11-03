from unittest import TestCase

from core.src.world.components import ComponentTypeEnum
from core.src.world.components.character import CharacterComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.name import NameComponent
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity, EntityID
from core.src.world.repositories.data_repository import RedisDataRepository
from etc import settings
from redis import StrictRedis


class TestWorldDataRepository(TestCase):
    def setUp(self):
        assert settings.INTEGRATION_TESTS
        assert settings.RUNNING_TESTS
        self.redis = StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_TEST_DB
        )
        self.redis.flushdb()
        self.sut = RedisDataRepository(self.redis)

    def tearDown(self):
        self.redis.flushdb()
        self.sut = RedisDataRepository(self.redis)

    def test_get_set(self):
        _entity_name = 'Billy Zinna'
        entity = Entity()
        entity.set(NameComponent(_entity_name))
        data = self.redis.hget('c:2:d', 1)
        self.assertIsNone(data)
        self.assertEqual(self.redis.getbit('c:2:m', 1), 0)
        self.assertEqual(self.redis.getbit('c:5:m', 1), 0)

        self.sut.save_entity(entity)
        self.assertEqual(self.redis.getbit('c:5:m', 1), 0)
        self.assertEqual(self.redis.getbit('c:3:m', 1), 0)
        name_on_component_storage = self.redis.hget('c:2:d', 1)
        self.assertEqual(name_on_component_storage, _entity_name.encode())
        name_on_entity_storage = self.redis.hget('e:1', 2)
        self.assertEqual(name_on_entity_storage, _entity_name.encode())

        response = self.sut.get_components_values_by_entities(
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
        response_by_components = self.sut.get_components_values_by_components(
            [entity], [NameComponent, CharacterComponent, ConnectionComponent]
        )
        self.assertEqual(
            {
                ComponentTypeEnum.NAME: {EntityID(1): 'Billy Zinna'},
                ComponentTypeEnum.CHARACTER: {EntityID(1): False},
                ComponentTypeEnum.CONNECTION: {EntityID(1): None}
            },
            response_by_components
        )
        entity.set(CharacterComponent(True))
        self.sut.update_entities(entity)
        self.assertTrue(self.redis.getbit('c:5:m', 1))
        self.assertIsNone(self.redis.hget('c:5:d', 1))
        response = self.sut.get_components_values_by_entities([entity], [CharacterComponent])

        self.assertEqual(
            {
                ComponentTypeEnum.CHARACTER: True,
            },
            response[EntityID(1)]
        )
        response = self.sut.get_components_values_by_entities(
            [entity],
            [CharacterComponent, NameComponent, PosComponent]
        )
        response_by_components = self.sut.get_components_values_by_components(
            [entity], [NameComponent, CharacterComponent, ConnectionComponent]
        )
        self.assertEqual(
            {
                ComponentTypeEnum.NAME: {EntityID(1): 'Billy Zinna'},
                ComponentTypeEnum.CHARACTER: {EntityID(1): True},
                ComponentTypeEnum.CONNECTION: {EntityID(1): None}
            },
            response_by_components
        )
        self.assertEqual(
            {
                ComponentTypeEnum.NAME: 'Billy Zinna',
                ComponentTypeEnum.CHARACTER: True,
                ComponentTypeEnum.POS: None
            },
            response[EntityID(1)]
        )
        self.sut.update_entities(entity.set(CharacterComponent(False)))
        response = self.sut.get_components_values_by_entities([entity], [CharacterComponent])

        self.assertEqual(
            {
                ComponentTypeEnum.CHARACTER: False,
            },
            response[EntityID(1)]
        )
        response_by_components = self.sut.get_components_values_by_components([entity], [CharacterComponent])
        self.assertEqual(
            {
                ComponentTypeEnum.CHARACTER: {EntityID(1): False},
            },
            response_by_components
        )
