from unittest import TestCase

from core.src.world.components.position import PositionComponent
from core.src.world.domain.area import Area


class TestArea(TestCase):
    def setUp(self):
        pass

    def test_relative_position(self):
        pos = PositionComponent(coord='2,3,0')
        pos2 = PositionComponent(coord='1,4,0')
        area = Area(pos, square_size=11)
        self.assertEqual(area.get_relative_position(pos2), 48)
        print('test area done')
