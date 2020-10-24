import copy
import enum
import typing
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

StructSubtypeDictSetAction = typing.NamedTuple(
    'StructSubtypeDictSetAction',
    (
        ('value', dict),
    )
)

StructSubtypeDictSetKeyValueAction = typing.NamedTuple(
    'StructSubtypeDictSetKeyValueAction',
    (
        ('key', str),
        ('value', typing.Union[int, str]),
    )
)


class _BasicStructType:
    value = None
    owner = None
    key = None

    def __str__(self):
        return str(self.value)

    def __eq__(self, v):
        return self.value == v

    def __bool__(self):
        return bool(self.value)

    def null(self):
        self.value = None
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubTypeSetNull())
        return self.owner


class _StructDictType(_BasicStructType):

    def __dict__(self):
        return self.value

    def __getitem__(self, key):
        return self.value[key]

    def __init__(self, owner, key, value=None):
        self.value = value or {}
        self.owner = owner
        self.key = key

    def set(self, value):
        assert isinstance(value, dict)
        self.value = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeDictSetAction(copy.copy(value)))
        return self.owner

    def get(self, key):
        return self.value[key]

    def set_value(self, key, value):
        assert isinstance(key, str)
        assert isinstance(value, (str, value))
        self.value[key] = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(StructSubtypeDictSetKeyValueAction(key, value))
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

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        try:
            res = self.value[self._n]
            self._n += 1
            return res
        except IndexError:
            raise StopIteration

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
            assert value in self.value
            self.value.remove(value)
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
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

        for k, v in kwargs.items():
            expected_type = self.meta[getattr(self.meta_enum, k)][1]
            assert type(v) == expected_type
            if expected_type == int:
                self._current_values[k] = _StructIntType(self, k, v)
            elif expected_type == list:
                self._current_values[k] = _StructListType(self, k, v)
            elif expected_type == str:
                self._current_values[k] = _StructStrType(self, k, v)
            elif expected_type == bool:
                self._current_values[k] = _StructBoolType(self, k, v)
            elif expected_type == dict:
                self._current_values[k] = _StructDictType(self, k, v)

        value = None
        super().__init__(value)

    def _bake_class(self):
        class MetaEnum(enum.Enum):
            pass

        self.meta_enum = MetaEnum
        for i, meta in enumerate(self.meta):
            setattr(self.meta_enum, meta[0], i)
            if meta[1] == int:
                self._current_values[meta[0]] = _StructIntType(self, meta[0], 0)
            elif meta[1] == list:
                self._current_values[meta[0]] = _StructListType(self, meta[0], [])
            elif meta[1] == str:
                self._current_values[meta[0]] = _StructStrType(self, meta[0], "")
            elif meta[1] == bool:
                self._current_values[meta[0]] = _StructBoolType(self, meta[0], False)
            elif meta[1] == dict:
                self._current_values[meta[0]] = _StructDictType(self, meta[0], {})
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
