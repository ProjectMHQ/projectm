import asyncio
from unittest import TestCase

from core.src.world.builder import map_repository
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.services.system_utils import get_redis_factory, RedisType
from tools.txt_map_to_redis import parse_lines
from etc import settings


class TestMapArea(TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()
        assert settings.INTEGRATION_TESTS
        assert settings.RUNNING_TESTS
        self.map = """
###########################################################
#..#...#...#...#...#...#...#...#...#...#...#...#...#...#..#
#..#...................................................#..#
#..#......................................................#
#......................................................#..#
#..#......................................................#
#..#...................................................#..#
#..#......................................................#
#......................................................#..#
#..#......................................................#
#..#...................................................#..#
#..#......................................................#
#......................................................#..#
#..#......................................................#
#..#...................................................#..#
#..#......................................................#
#......................................................#..#
#..#......................................................#
#..##########..############..###########.##########....#..#
#.........................................................#
###########################################################
"""
        self.content = parse_lines([x for x in self.map.split('\n') if x])
        self.loop.run_until_complete(self.setup_map())

    async def setup_map(self):
        await (await get_redis_factory(RedisType.QUEUES)()).flushdb()
        await map_repository.set_rooms(*self.content)

    async def _get_map(self, x, y):
        map_repository.max_x = 58
        map_repository.max_y = 20
        size = 9
        a = Area(center=PosComponent([x, y, 0]), square_size=size)
        q = [(x and x.terrain.value or 0) for x in await a.get_rooms()]
        assert len(q) == size * size, len(q)
        c = {0: " ", 1: "#", 2: "."}
        lines = []
        for i in range(0, len(q) + size, size):
            lines.append([c[x] for x in q[i - size:i]])
        ch = 0
        half = int((size * size) / 2) + 1
        for i, line in enumerate(lines):
            x = ch + len(line)
            if x > half:
                lines[i][len(line) - (half - ch)] = 'X'
                break
            ch += len(line)
        m = ""
        for line in lines:
            m += "".join(line) + '\n'
        return m, q

    def test_map_1(self):
        loop = asyncio.get_event_loop()
        m, q = loop.run_until_complete(self._get_map(5, 5))
        expected = """
        ..#......
        .........
        ..#......
        ..#......
        ..#.X....
        .........
        ..#......
        ..#######
        .........
        """.replace('        ', '')
        self.assertEqual(m.replace(' ', ''), expected)
        expected_array = [
            2, 2, 1, 2, 2, 2, 2, 2, 2,
            2, 2, 2, 2, 2, 2, 2, 2, 2,
            2, 2, 1, 2, 2, 2, 2, 2, 2,
            2, 2, 1, 2, 2, 2, 2, 2, 2,
            2, 2, 1, 2, 2, 2, 2, 2, 2,
            2, 2, 2, 2, 2, 2, 2, 2, 2,
            2, 2, 1, 2, 2, 2, 2, 2, 2,
            2, 2, 1, 1, 1, 1, 1, 1, 1,
            2, 2, 2, 2, 2, 2, 2, 2, 2
        ]
        self.assertEqual(q, expected_array)

    def test_map_2(self):
        loop = asyncio.get_event_loop()
        m, q = loop.run_until_complete(self._get_map(0, 0))
        expected = """
             #....
             #..#.
             #..##
             #....
             X####
            
            
            
            
        """.replace(' ', '')
        self.assertEqual(m.replace(' ', ''), expected)
        expected_array = [
            0, 0, 0, 0, 1, 2, 2, 2, 2,
            0, 0, 0, 0, 1, 2, 2, 1, 2,
            0, 0, 0, 0, 1, 2, 2, 1, 1,
            0, 0, 0, 0, 1, 2, 2, 2, 2,
            0, 0, 0, 0, 1, 1, 1, 1, 1,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0
        ]
        self.assertEqual(q, expected_array)

    def test_map_3(self):
        loop = asyncio.get_event_loop()
        m, q = loop.run_until_complete(self._get_map(58, 20))
        expected = """




        ####X
        .#..#
        .#..#
        ....#
        .#..#
        """.replace(' ', '')
        self.assertEqual(m.replace(' ', ''), expected)
        expected_array = [
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            1, 1, 1, 1, 1, 0, 0, 0, 0,
            2, 1, 2, 2, 1, 0, 0, 0, 0,
            2, 1, 2, 2, 1, 0, 0, 0, 0,
            2, 2, 2, 2, 1, 0, 0, 0, 0,
            2, 1, 2, 2, 1, 0, 0, 0, 0
        ]
        self.assertEqual(q, expected_array)

    def test_map_4(self):
        loop = asyncio.get_event_loop()
        m, q = loop.run_until_complete(self._get_map(0, 20))
        expected = """



        
             X####
             #..#.
             #..#.
             #..#.
             #....
        """.replace(' ', '')
        self.assertEqual(m.replace(' ', ''), expected)
        expected_array = [
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 1, 1, 1, 1, 1,
            0, 0, 0, 0, 1, 2, 2, 1, 2,
            0, 0, 0, 0, 1, 2, 2, 1, 2,
            0, 0, 0, 0, 1, 2, 2, 1, 2,
            0, 0, 0, 0, 1, 2, 2, 2, 2
        ]
        self.assertEqual(q, expected_array)

    def test_map_5(self):
        loop = asyncio.get_event_loop()
        m, q = loop.run_until_complete(self._get_map(58, 0))
        expected = """
        .#..#
        ....#
        .#..#
        ....#
        ####X
        
        
        
        
""".replace(' ', '')
        self.assertEqual(m.replace(' ', ''), expected)
        expected_array = [
            2, 1, 2, 2, 1, 0, 0, 0, 0,
            2, 2, 2, 2, 1, 0, 0, 0, 0,
            2, 1, 2, 2, 1, 0, 0, 0, 0,
            2, 2, 2, 2, 1, 0, 0, 0, 0,
            1, 1, 1, 1, 1, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0
        ]
        self.assertEqual(q, expected_array)
