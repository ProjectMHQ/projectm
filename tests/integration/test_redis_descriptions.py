import asyncio

from core.src.world.builder import descriptions_repository
from etc import settings
from unittest import TestCase


class TestRedisDescriptionsRepository(TestCase):
    def setUp(self):
        assert settings.INTEGRATION_TESTS
        assert settings.RUNNING_TESTS
        self.sut = descriptions_repository

    async def async_test_descriptions(self):
        await self.sut.save_entity_description(1, 'pippo', 'pluto')
        des = await self.sut.get_entity_description(1)
        self.assertEqual(des, {'entity_id': 1, 'title': 'pippo', 'description': 'pluto'})
        await self.sut.save_entity_description(1, 'pippo', 'pluto2')
        des = await self.sut.get_entity_description(1)
        self.assertEqual(des, {'entity_id': 1, 'title': 'pippo', 'description': 'pluto2'})
        exp_res = {}
        for x in range(0, 100):
            await self.sut.save_terrain_description(
                x,
                'terrain {} title'.format(x),
                'terrain {} description'.format(x)
            )
            exp_res[x] = {'title': 'terrain {} title'.format(x), 'description': 'terrain {} description'.format(x)}
        terrainz = await self.sut.get_all_terrains_descriptions()
        self.assertEqual(terrainz, exp_res)

    def test(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test_descriptions())
