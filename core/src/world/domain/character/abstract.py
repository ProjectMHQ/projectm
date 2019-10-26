import abc
import enum
import typing


class CharacterAbstract(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    @property
    def character_id(self) -> str:
        pass

    @abc.abstractmethod
    @property
    def pos(self) -> typing.NamedTuple:
        pass

    @abc.abstractmethod
    def set_pos(self, pos: typing.NamedTuple) -> 'CharacterAbstract':
        pass

    @abc.abstractmethod
    def set_name(self, name: str) -> 'CharacterAbstract':
        pass

    @abc.abstractmethod
    @classmethod
    def from_dict(cls, values: typing.Dict) -> 'CharacterAbstract':
        pass

    @abc.abstractmethod
    @classmethod
    def new(cls, character_id: str, name: str) -> 'CharacterAbstract':
        pass

    @abc.abstractmethod
    def set_id(self, character_id: str) -> 'CharacterAbstract':
        pass

    @abc.abstractmethod
    @classmethod
    def login(cls, character_id: str, repo: typing.Optional[typing.NamedTuple]=None):
        pass

    @abc.abstractmethod
    def logout(self, repo: typing.Optional[typing.NamedTuple]=None):
        pass

    @abc.abstractmethod
    def look(self, direction: enum.IntEnum):
        raise NotImplementedError
