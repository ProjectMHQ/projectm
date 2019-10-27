import abc
import enum
import typing


class CharacterAbstract(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def character_id(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def pos(self) -> typing.NamedTuple:
        pass

    @abc.abstractmethod
    def set_pos(self, pos: typing.NamedTuple) -> 'CharacterAbstract':
        pass

    @abc.abstractmethod
    def set_name(self, name: str) -> 'CharacterAbstract':
        pass

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, values: typing.Dict) -> 'CharacterAbstract':
        pass

    @classmethod
    @abc.abstractmethod
    def new(cls, character_id: str, name: str) -> 'CharacterAbstract':
        pass

    @abc.abstractmethod
    def set_id(self, character_id: str) -> 'CharacterAbstract':
        pass

    @classmethod
    @abc.abstractmethod
    def login(cls, character_id: str, character_name: str, repo: typing.Optional[typing.NamedTuple]=None):
        pass

    @abc.abstractmethod
    def logout(self, repo: typing.Optional[typing.NamedTuple]=None):
        pass

    @abc.abstractmethod
    def look(self, direction: enum.IntEnum):
        raise NotImplementedError
