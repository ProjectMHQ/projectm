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
    def pos(self) -> typing.Tuple:
        pass  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def from_model(cls, model):
        pass  # pragma: no cover

    @abc.abstractmethod
    def as_dict(self, context=None):
        pass  # pragma: no cover

    @abc.abstractmethod
    def ensure_can_authenticate(self):
        pass  # pragma: no cover
