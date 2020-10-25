import enum
import typing
from ast import literal_eval

from core.src.world.components.base import ComponentType


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

    def __iter__(self):
        return iter(self.value)

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

    def set(self, value):
        assert isinstance(value, str)
        self.value = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeStrSetAction(value))
        return self.owner


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
        assert isinstance(value, int)
        self.value = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeIntSetAction(value))
        return self.owner


class _StructListType(_BasicStructType):
    def __init__(self, owner, key, value=None):
        self.value = value or []
        self.owner = owner
        self.key = key

    def __getitem__(self, item):
        return self.value[item]

    def append(self, *values: int):
        for value in values:
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


class StructComponent(ComponentType):

    is_struct = True
    meta = ()
    indexes = ()

    @staticmethod
    def _validate_param_for_list(v, pending_changes):
        if isinstance(v, StructSubtypeListAction):
            pending_changes.append(v)
            return True
        if not isinstance(v, (list, tuple)):
            return False
        else:
            for x in v:
                if not isinstance(x, StructSubtypeListAction):
                    return False
                else:
                    pending_changes.append(x)

    @property
    def current_values(self) -> typing.Dict:
        return self._current_values

    @property
    def value(self) -> typing.Dict:
        """
        Return the current values loaded into the component
        """
        return self._current_values

    def __init__(self, **kwargs):
        self._valid_values = []
        self.pending_changes = {}
        self._current_values = {}
        self._bake_class()
        self.bounds = {}

        for k, v in kwargs.items():
            expected_type = self.meta[getattr(self.meta_enum, k)][1]
            assert type(v) == expected_type
            self._set_value(k, v)

        value = None
        super().__init__(value)

    def remove_bounds(self):
        self.bounds = {}
        return self

    def _bake_class(self):
        class MetaEnum(enum.Enum):
            pass

        self.meta_enum = MetaEnum
        for i, meta in enumerate(self.meta):
            setattr(self.meta_enum, meta[0], i)
            values = {int: 0, list: [], str: "", bool: False, dict: {}}
            self._set_value(meta[0], values[meta[1]])

    def _set_value(self, key, value):
        expected_type = self.meta[getattr(self.meta_enum, key)][1]
        if expected_type == int:
            self._current_values[key] = _StructIntType(self, key, value)
        elif expected_type == list:
            self._current_values[key] = _StructListType(self, key, value)
        elif expected_type == str:
            self._current_values[key] = _StructStrType(self, key, value)
        elif expected_type == bool:
            self._current_values[key] = _StructBoolType(self, key, value)
        elif expected_type == dict:
            self._current_values[key] = _StructDictType(self, key, value)
        else:
            raise ValueError

    def __getattr__(self, name):
        try:
            return self._current_values[name]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'.\nvalid attributes: {2}"
            raise AttributeError(msg.format(type(self).__name__, name, ', '.join(self._current_values.keys())))

    def has_index(self, key):
        return key in self.indexes

    def get_subtype(self, key):
        return self.meta[getattr(self.meta_enum, key)][1]

    def load_value(self, key, value):
        expected_type = self.meta[getattr(self.meta_enum, key)][1]
        if not value:
            self._set_value(key, value)
        elif expected_type is list:
            self._set_value(key, [int(x) for x in value])
        elif expected_type is dict:
            self._set_value(key, {k.decode(): v.decode() for k, v in value.items()})
        elif expected_type is bool:
            self._set_value(key, bool(int(value)))
        elif expected_type is str:
            self._set_value(key, value.decode())
        elif expected_type is int:
            self._set_value(key, int(value))
        return self
