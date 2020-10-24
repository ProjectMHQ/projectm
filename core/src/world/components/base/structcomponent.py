import enum
import typing
from core.src.world.components.base import ComponentType


_ListAction = typing.NamedTuple(
    '_ListAction',
    (
        ('action_type', str),
        ('values', list)
    )
)

_IntIncrAction = typing.NamedTuple(
    '_IncrAction',
    (
        ('value', int),
    )
)

_IntSetAction = typing.NamedTuple(
    '_IntSetAction',
    (
        ('value', int),
    )
)

_StrSetAction = typing.NamedTuple(
    '_StrSetAction',
    (
        ('value', str),
    )
)


class _StructStrType:
    def __init__(self, owner, key, value=""):
        self.value = value
        self.owner = owner
        self.key = key

    def __str__(self):
        return str(self.value)

    def __eq__(self, v):
        return self.value == v

    def set(self, value):
        assert isinstance(value, str)
        self.value = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(_StrSetAction(value))
        return self.owner


class _StructIntType:
    def __init__(self, owner, key, value=0):
        self.value = value
        self.owner = owner
        self.key = key

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)

    def __eq__(self, v):
        return self.value == v

    def incr(self, value: int):
        assert isinstance(value, int)
        self.value += value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(_IntIncrAction(value))
        return self.owner

    def set(self, value):
        assert isinstance(value, int)
        self.value = value
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(_IntSetAction(value))
        return self.owner


class _StructListType:
    def __init__(self, owner, key, value=None):
        self.value = value or []
        self.owner = owner
        self.key = key

    def __eq__(self, value):
        return self.value == value

    def __iter__(self):
        self._n = 0
        return self

    def __str__(self):
        return str(self.value)

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
        self.owner.pending_changes[self.key].append(_ListAction('append', list(values)))
        return self.owner

    def remove(self, *values: int):
        for value in values:
            assert isinstance(value, int)
            assert value in self.value
            self.value.remove(value)
        if not self.owner.pending_changes.get(self.key):
            self.owner.pending_changes[self.key] = []
        self.owner.pending_changes[self.key].append(_ListAction('remove', list(values)))
        return self.owner


class StructComponent(ComponentType):

    is_struct = True
    meta = ()
    indexes = ()

    @staticmethod
    def _validate_param_for_list(v, pending_changes):
        if isinstance(v, _ListAction):
            pending_changes.append(v)
            return True
        if not isinstance(v, (list, tuple)):
            return False
        else:
            for x in v:
                if not isinstance(x, _ListAction):
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
            else:
                raise ValueError

    def __getattr__(self, name):
        try:
            return self._current_values[name]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'.\nvalid attributes: {2}"
            raise AttributeError(msg.format(type(self).__name__, name, ', '.join(self._current_values.keys())))

    def _getter(self, name, value):
        expected_type = self.meta[self.meta_enum(name).value][1]
        assert type(value) == expected_type
        if expected_type == int:
            return self._current_values.get(name, _StructIntType(self, name, value))
        elif expected_type == list:
            return self._current_values.get(name, _StructListType(self, name, value))
        elif expected_type == str:
            return self._current_values.get(name, "")

    def has_index(self, key):
        return key in self.indexes

    def is_subtype_array(self, key):
        return self.meta[getattr(self.meta_enum, key)][1] == list

    def is_subtype_string(self, key):
        return self.meta[getattr(self.meta_enum, key)][1] == str

    def is_subtype_boolean(self, key):
        return self.meta[getattr(self.meta_enum, key)][1] == bool

    def is_subtype_int(self, key):
        return self.meta[getattr(self.meta_enum, key)][1] == int

    def get_subtype(self, key):
        return self.meta[getattr(self.meta_enum, key)][1]
