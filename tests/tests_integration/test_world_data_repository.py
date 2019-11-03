from unittest import TestCase

from core.src.world.components import ComponentTypeEnum
from core.src.world.components.character import CharacterComponent
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
        self.redis.flushall()
        self.sut = RedisDataRepository(self.redis)

    def tearDown(self):
        self.redis.flushall()
        self.sut = RedisDataRepository(self.redis)

    def test_get_set(self):
        _entity_name = 'Billy Zinna'
        entity = Entity()
        entity.set(NameComponent(_entity_name))
        self.sut.save_entity(entity)
        data = self.redis.hget('c:2:d', 1)
        self.assertEqual(data, _entity_name.encode())

        response = self.sut.get_components_values_by_entities([entity], [NameComponent, CharacterComponent])
        self.assertEqual(
            {
                ComponentTypeEnum.NAME: b'Billy Zinna',
                ComponentTypeEnum.CHARACTER: None
            },
            response[EntityID(1)]
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
        self.assertEqual(
            {
                ComponentTypeEnum.NAME: b'Billy Zinna',
                ComponentTypeEnum.CHARACTER: True,
                ComponentTypeEnum.POS: None
            },
            response[EntityID(1)]
        )
