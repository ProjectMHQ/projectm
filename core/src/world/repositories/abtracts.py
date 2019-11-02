import abc
import typing


class RedisRepositoryAbstract(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def exists(self, character_id: str):
        pass

    @abc.abstractmethod
    def create(self, character_id: str, name: str) -> typing.Dict:
        pass

    @abc.abstractmethod
    def get(self, character_id: str, *values) -> typing.Dict:
        pass

    @abc.abstractmethod
    def set(self, character_id: str, *values: typing.Tuple[str, typing.Any]):
        pass
