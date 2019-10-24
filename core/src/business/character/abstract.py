import abc
import enum
import typing


class CharacterDOAbstract(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def character_id(self) -> str:
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def user_id(self) -> str:
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def gender(self) -> enum.Enum:
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def at_coordinates(self) -> typing.Tuple:
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def race(self) -> enum.Enum:
        pass  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def from_model(cls, model):
        pass  # pragma: no cover

    @abc.abstractmethod
    def as_dict(self, context=None):
        pass  # pragma: no cover


class CharacterServiceAbstract(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def exists(self, character: CharacterDOAbstract):
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_coordinates(self, character: CharacterDOAbstract):
        pass  # pragma: no cover
