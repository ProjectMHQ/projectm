from unittest import TestCase

from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area


class TestArea(TestCase):
    def setUp(self):
        pass

    def test_relative_position(self):
        pos = PosComponent([2, 3, 0])
        pos2 = PosComponent([1, 4, 0])
        area = Area(pos)
        self.assertEqual(area.get_relative_position(pos2), 48)

