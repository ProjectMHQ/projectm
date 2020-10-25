import unittest
from core.src.world.components.base.structcomponent import \
    StructComponent, StructSubtypeListAction, StructSubtypeIntIncrAction, StructSubtypeIntSetAction, \
    StructSubtypeStrSetAction, StructSubTypeSetNull, \
    StructSubTypeBoolOn, StructSubTypeBoolOff, StructSubTypeDictSetKeyValueAction, StructSubTypeDictRemoveKeyValueAction


class TestStructComponent(unittest.TestCase):
    def setUp(self):
        pass

    def test_struct_component(self):
        class InventoryComponent(StructComponent):
            meta = (('content', list), ('weight', int), ('label', str))

        inventory = InventoryComponent(content=[30])
        for x in inventory.content:
            self.assertEqual(x, 30)
        inventory.content.append(42, 26)
        self.assertEqual([30, 42, 26], inventory.content)
        self.assertEqual(inventory.pending_changes['content'][0].type, 'append')
        self.assertEqual(inventory.pending_changes['content'][0].values, [42, 26])
        inventory.content.remove(42).content.append(99)
        self.assertEqual(inventory.pending_changes['content'][1].type, 'remove')
        self.assertEqual(inventory.pending_changes['content'][1].values, [42])
        self.assertEqual(inventory.content, [30, 26, 99])
        expected_pending_changes = {
            'content': [
                StructSubtypeListAction(type='append', values=[42, 26]),
                StructSubtypeListAction(type='remove', values=[42]),
                StructSubtypeListAction(type='append', values=[99])
            ]
        }
        self.assertEqual(expected_pending_changes, inventory.pending_changes)

    def test_struct_int(self):
        class InventoryComponent(StructComponent):
            meta = (('content', list), ('weight', int), ('label', str))

        inventory = InventoryComponent(weight=33)
        self.assertEqual(inventory.weight, 33)
        inventory.weight.incr(10)
        self.assertEqual(inventory.weight, 43)
        expected_pending_changes = {'weight': [StructSubtypeIntIncrAction(value=10)]}
        self.assertEqual(inventory.pending_changes, expected_pending_changes)
        inventory.weight.incr(-3)
        self.assertEqual(inventory.weight, 40)
        expected_pending_changes = {'weight': [
            StructSubtypeIntIncrAction(value=10), StructSubtypeIntIncrAction(value=-3)
        ]}
        self.assertEqual(inventory.pending_changes, expected_pending_changes)
        inventory.weight.set(42)
        expected_pending_changes = {'weight': [
            StructSubtypeIntIncrAction(value=10),
            StructSubtypeIntIncrAction(value=-3),
            StructSubtypeIntSetAction(value=42)
        ]}
        self.assertEqual(inventory.pending_changes, expected_pending_changes)
        self.assertEqual(inventory.weight, 42)

    def test_struct_str(self):
        class InventoryComponent(StructComponent):
            meta = (('content', list), ('weight', int), ('label', str))
            _indexes = ('content',)

        inventory = InventoryComponent(label='ciao')
        self.assertEqual(inventory.label, 'ciao')
        inventory.content.append(30).weight.set(10).weight.incr(5).label.set('prova')
        self.assertEqual(
            inventory.pending_changes,
            {
                'content': [StructSubtypeListAction(type='append', values=[30])],
                'weight': [StructSubtypeIntSetAction(value=10), StructSubtypeIntIncrAction(value=5)],
                'label': [StructSubtypeStrSetAction(value='prova')]
            }
        )
        self.assertEqual(inventory.weight, 15)
        self.assertEqual(inventory.content, [30])
        self.assertEqual(inventory.label, 'prova')

        self.assertEqual(inventory.get_subtype('weight'), int)
        self.assertEqual(inventory.get_subtype('content'), list)
        self.assertEqual(inventory.get_subtype('label'), str)

        self.assertTrue(inventory.has_index('content'))

    def test_struct_null(self):
        class InventoryComponent(StructComponent):
            meta = (('content', list), ('weight', int), ('label', str))
            _indexes = ('content',)

        inventory = InventoryComponent(label='ciao', weight=11, content=[33])
        self.assertEqual(inventory.label, 'ciao')
        self.assertEqual(inventory.weight, 11)
        self.assertEqual(inventory.content, [33])
        inventory.content.null().label.null().weight.null()

        self.assertEqual(
            inventory.pending_changes,
            {
                'content': [StructSubTypeSetNull()],
                'label': [StructSubTypeSetNull()],
                'weight': [StructSubTypeSetNull()]
            }
        )
        self.assertEqual(inventory.get_subtype('weight'), int)
        self.assertEqual(inventory.get_subtype('content'), list)
        self.assertEqual(inventory.get_subtype('label'), str)

        self.assertTrue(inventory.has_index('content'))

        self.assertEqual(inventory.content, None)
        self.assertEqual(inventory.label, None)
        self.assertEqual(inventory.weight, None)

        self.assertFalse(inventory.content)
        self.assertFalse(inventory.label)
        self.assertFalse(inventory.weight)

        self.assertIsNotNone(inventory.content)
        self.assertIsNotNone(inventory.label)
        self.assertIsNotNone(inventory.weight)

    def test_sucavar(self):
        class Container(StructComponent):
            meta = (('happy', bool), ('attrs', dict))

        container = Container()
        container.happy.set(True).attrs.set('pippo', 'pluto')
        self.assertEqual(
            container.pending_changes,
            {
                'attrs': [StructSubTypeDictSetKeyValueAction(key='pippo', value='pluto')],
                'happy': [StructSubTypeBoolOn()]
            }
        )
        self.assertTrue(container.happy)
        self.assertEqual(container.attrs['pippo'], 'pluto')
        r = {'pippo': 'pluto'}

        for k, v in container.attrs.items():
            self.assertEqual(v, r[k])

        container.attrs.set("pippo", "pippa").happy.set(False)
        self.assertEqual(
            container.pending_changes,
            dict(attrs=[StructSubTypeDictSetKeyValueAction(key='pippo', value='pluto'),
                        StructSubTypeDictSetKeyValueAction(key='pippo', value='pippa')],
                 happy=[StructSubTypeBoolOn(), StructSubTypeBoolOff()])
        )
        self.assertEqual(container.attrs['pippo'], 'pippa')
        self.assertEqual(container.attrs.get('pippo'), 'pippa')
        self.assertFalse(container.happy)
        container.attrs.remove('pippo')
        self.assertEqual(len(container.attrs), 0)
        self.assertEqual(
            container.pending_changes,
            dict(attrs=[StructSubTypeDictSetKeyValueAction(key='pippo', value='pluto'),
                        StructSubTypeDictSetKeyValueAction(key='pippo', value='pippa'),
                        StructSubTypeDictRemoveKeyValueAction(key='pippo')],
                 happy=[StructSubTypeBoolOn(), StructSubTypeBoolOff()])
        )

