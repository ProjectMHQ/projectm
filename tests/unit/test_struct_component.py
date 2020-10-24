import unittest
from core.src.world.components.base.structcomponent import \
    StructComponent, _ListAction, _IntIncrAction, _IntSetAction, _StrSetAction


class TestInventoryComponent(unittest.TestCase):
    def setUp(self):
        pass

    def test_inventory_component(self):
        class InventoryComponent(StructComponent):
            meta = (('content', list), ('weight', int), ('label', str))

        inventory = InventoryComponent(content=[30])
        for x in inventory.content:
            self.assertEqual(x, 30)
        inventory.content.append(42, 26)
        self.assertEqual([30, 42, 26], inventory.content)
        self.assertEqual(inventory.pending_changes['content'][0].action_type, 'append')
        self.assertEqual(inventory.pending_changes['content'][0].values, [42, 26])
        inventory.content.remove(42).content.append(99)
        self.assertEqual(inventory.pending_changes['content'][1].action_type, 'remove')
        self.assertEqual(inventory.pending_changes['content'][1].values, [42])
        self.assertEqual(inventory.content, [30, 26, 99])
        expected_pending_changes = {
            'content': [
                _ListAction(action_type='append', values=[42, 26]),
                _ListAction(action_type='remove', values=[42]),
                _ListAction(action_type='append', values=[99])
            ]
        }
        self.assertEqual(expected_pending_changes, inventory.pending_changes)

    def test_inventory_int(self):
        class InventoryComponent(StructComponent):
            meta = (('content', list), ('weight', int), ('label', str))

        inventory = InventoryComponent(weight=33)
        self.assertEqual(inventory.weight, 33)
        inventory.weight.incr(10)
        self.assertEqual(inventory.weight, 43)
        expected_pending_changes = {'weight': [_IntIncrAction(value=10)]}
        self.assertEqual(inventory.pending_changes, expected_pending_changes)
        inventory.weight.incr(-3)
        self.assertEqual(inventory.weight, 40)
        expected_pending_changes = {'weight': [_IntIncrAction(value=10), _IntIncrAction(value=-3)]}
        self.assertEqual(inventory.pending_changes, expected_pending_changes)
        inventory.weight.set(42)
        expected_pending_changes = {'weight': [_IntIncrAction(value=10),
                                               _IntIncrAction(value=-3),
                                               _IntSetAction(value=42)]}
        self.assertEqual(inventory.pending_changes, expected_pending_changes)
        self.assertEqual(inventory.weight, 42)

    def test_inventory_str(self):
        class InventoryComponent(StructComponent):
            meta = (('content', list), ('weight', int), ('label', str))
        inventory = InventoryComponent(label='ciao')
        self.assertEqual(inventory.label, 'ciao')
        inventory.content.append(30).weight.set(10).weight.incr(5).label.set('prova')
        self.assertEqual(
            inventory.pending_changes,
            {
                'content': [_ListAction(action_type='append', values=[30])],
                'weight': [_IntSetAction(value=10), _IntIncrAction(value=5)],
                'label': [_StrSetAction(value='prova')]
            }
        )
        self.assertEqual(inventory.weight, 15)
        self.assertEqual(inventory.content, [30])
        self.assertEqual(inventory.label, 'prova')

        self.assertEqual(inventory.get_subtype('weight'), int)
        self.assertEqual(inventory.get_subtype('content'), list)
        self.assertEqual(inventory.get_subtype('label'), str)
