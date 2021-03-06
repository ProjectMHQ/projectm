import enum
import typing
from core.src.world.components.base.abstract import ComponentType

StructSubtypeListAction = typing.NamedTuple(
    'StructSubtypeListAction',
    (
        ('type', str),
        ('values', list)
    )
)

StructSubtypeIntIncrAction = typing.NamedTuple(
    'StructSubtypeIntIncrAction',
    (
        ('value', int),
    )
)

StructSubtypeIntSetAction = typing.NamedTuple(
    'StructSubtypeIntSetAction',
    (
        ('value', int),
    )
)

StructSubtypeStrSetAction = typing.NamedTuple(
    'StructSubtypeStrSetAction',
    (
        ('value', str),
    )
)

StructSubtypeBoolSetAction = typing.NamedTuple(
    'StructSubtypeBoolSetAction',
    (
        ('value', bool),
    )
)

StructSubTypeSetNull = typing.NamedTuple(
    'StructSubTypeSetNull',
    ()
)

StructSubTypeBoolOn = typing.NamedTuple(
    'StructSubTypeBoolOn',
    ()
)

StructSubTypeBoolOff = typing.NamedTuple(
    'StructSubTypeBoolOff',
    ()
)

StructSubTypeDictSetKeyValueAction = typing.NamedTuple(
    'StructSubTypeDictSetKeyValueAction',
    (
        ('key', str),
        ('value', typing.Union[int, str, None, bool]),
    )
)


StructSubTypeDictRemoveKeyValueAction = typing.NamedTuple(
    'StructSubTypeDictRemoveKeyValueAction',
    (
        ('key', str),
    )
)


class _BasicStructType:
    value = None
    owner = None
    key = None

    def __repr__(self):
        return repr(self.value)

    def __add__(self, other):
        return self.value + other

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, v):
        return self.value == v

    def __ne__(self, v):
        return self.value != v

    def __bool__(self):
        return bool(self.value)

    def __hash__(self):
        return hash(self.value)

    def __and__(self, other):
        return other and self.value

    def null(self):
        self.value = None
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubTypeSetNull())
        return self.owner

    def build_updates_from_scratch(self):
        raise NotImplementedError


class _StructDictType(_BasicStructType):

    def __dict__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, item):
        return self.value[item]

    def items(self):
        return self.value.items()

    def keys(self):
        return self.value.keys()

    def values(self):
        return self.value.values()

    def __init__(self, owner, key, value=None):
        self.value = value or {}
        self.owner = owner
        self.key = key

    def build_updates_from_scratch(self):
        for k, v in self.value.items():
            if not v:
                self.remove(k)
            else:
                self.set(k, v)

    def remove(self, key):
        assert isinstance(key, str)
        self.value.pop(key)
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubTypeDictRemoveKeyValueAction(key))
        return self.owner

    def get(self, key):
        return self.value.get(key, None)

    def has_key(self, key):
        try:
            _ = self.value[key]
            return True
        except KeyError:
            return False

    def set(self, key: str, value: typing.Union[str, int, bool, None]):
        assert isinstance(key, str)
        self.value[key] = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubTypeDictSetKeyValueAction(key, value))
        return self.owner


class _StructStrType(_BasicStructType):
    def __init__(self, owner, key, value=""):
        self.value = value
        self.owner = owner
        self.key = key

    def __iter__(self):
        return iter(self.value)

    def startswith(self, value):
        return self.value.startswith(value)

    def set(self, value):
        value = value if value is not None else ''
        assert isinstance(value, str)
        self.value = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeStrSetAction(value))
        return self.owner

    def build_updates_from_scratch(self):
        self.set(self.value)
        return self


class _StructBoolType(_BasicStructType):
    def __init__(self, owner, key, value=False):
        self.value = value
        self.owner = owner
        self.key = key

    def set(self, value: bool):
        assert isinstance(value, bool)
        self.value = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        action = StructSubTypeBoolOff() if not value else StructSubTypeBoolOn()
        self.owner.pending_changes[self.key].append(action)
        return self.owner

    def enable(self):
        self.set(True)
        return self.owner

    def disable(self):
        self.set(False)
        return self.owner

    def build_updates_from_scratch(self):
        _ = self.enable() if self.value else self.disable()
        return self


class _StructIntType(_BasicStructType):
    def __init__(self, owner, key, value=0):
        self.value = value
        self.owner = owner
        self.key = key

    def __int__(self):
        return self.value

    def incr(self, value: int):
        assert isinstance(value, int)
        self.value += value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeIntIncrAction(value))
        return self.owner

    def set(self, value):
        value = value if value is not None else 0
        assert isinstance(value, int), value
        self.value = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeIntSetAction(value))
        return self.owner

    def build_updates_from_scratch(self):
        self.set(self.value)
        return self


class _StructListType(_BasicStructType):
    def __init__(self, owner, key, value=None):
        self.value = value or []
        self.owner = owner
        self.key = key

    def __getitem__(self, item):
        return self.value[item]

    def __iter__(self):
        return iter(self.value)

    def append(self, *values: int):
        for value in values:
            print(values, self.value)
            assert isinstance(value, int)
            assert value not in self.value
            self.value.append(value)
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeListAction('append', list(values)))
        return self.owner

    def remove(self, *values: int):
        for value in values:
            assert isinstance(value, int)
            if value in self.value:
                self.value.remove(value)
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        if not self.owner.bounds.get(self.key):
            self.owner.bounds[self.key] = []
        self.owner.bounds[self.key].append(StructSubtypeListAction('remove', list(values)))
        self.owner.pending_changes[self.key].append(StructSubtypeListAction('remove', list(values)))
        return self.owner

    def build_updates_from_scratch(self):
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeListAction('overwrite', self.value))
        return self.owner


class StructComponent(ComponentType):
    """
    Example:

    class InventoryComponent(StructComponent):
        enum = ComponentTypeEnum.INVENTORY
        libname = "inventory"

        _meta = (
            ("content", list),
            ("current_weight", int)
        )

    """
    meta = ()
    indexes = ()
    defaults = ()

    @classmethod
    def is_active(cls):
        return True

    @property
    def is_struct(self):
        return True

    @property
    def value(self) -> typing.Dict:
        """
        Return the current values loaded into the component
        """
        return self._current_values

    def __init__(self, **kwargs):
        self.pending_changes = {}
        self.bounds = {}
        self._current_values = {}
        self._bake_class()
        self._reserved_names = {'meta', 'indexes', 'defaults'}

        for k, v in kwargs.items():
            assert k not in self._reserved_names
            assert not getattr(self, k, None)
            expected_type = self.meta[getattr(self.meta_enum, k)][1]
            if v is not None:
                assert type(v) == expected_type, (type(v), expected_type)
            load_value_in_struct_component(self, k, v)

        value = None
        super().__init__(value)

    def build_values_as_changes(self):
        for k, values in self._current_values.items():
            if k not in self.defaults:
                values.build_updates_from_scratch()

    def remove_bounds(self):
        self.bounds = {}
        return self

    def _bake_class(self):
        class MetaEnum(enum.Enum):
            pass

        self.meta_enum = MetaEnum
        for i, meta in enumerate(self.meta):
            setattr(self.meta_enum, meta[0], i)
            values = {int: b'0', list: [], str: b"", bool: b'0', dict: {}}
            load_value_in_struct_component(self, meta[0], values[meta[1]])

    def __getattr__(self, name):
        try:
            return self.current_values[name]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'.\nvalid attributes: {2}"
            raise AttributeError(msg.format(type(self).__name__, name, ', '.join(self._current_values.keys())))

    def has_index(self, key):
        for x in self.indexes:
            if key == x[0]:
                return True
        return False

    def get_index_type(self, key):
        for x in self.indexes:
            if key == x[0]:
                return x[1]

    def has_default(self, key):
        return key in self.defaults

    @classmethod
    def get_subtype(cls, key):
        return {k[0]: k[1] for k in cls.meta}[key]

    @property
    def current_values(self):
        return self._current_values

    def get_value(self, k):
        return self._current_values[k].value


def load_value_in_struct_component(component, key, value):
    def _enc(x):
        return isinstance(x, bytes) and x.decode() or x

    expected_type = component.meta[getattr(component.meta_enum, key)][1]
    if expected_type is list:
        component.current_values[key] = _StructListType(component, key, value and [int(x) for x in value])
    elif expected_type is dict:
        component.current_values[key] = _StructDictType(
            component, key, value and {_enc(k): _enc(v) for k, v in value.items()}
        )
    elif expected_type is bool:
        if value is not None and not isinstance(value, bool):
            v = bool(int(value.decode()))
        else:
            v = value
        component.current_values[key] = _StructBoolType(component, key, v)
    elif expected_type is str:
        if value is not None and not isinstance(value, str):
            v = value.decode()
        else:
            v = value
        component.current_values[key] = _StructStrType(component, key, v)
    elif expected_type is int:
        if value is not None and not isinstance(value, int):
            v = int(value.decode())
        else:
            v = value
        component.current_values[key] = _StructIntType(component, key, v)
    return component
