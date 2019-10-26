import typing
from core.src.world.domain.character.abstract import CharacterAbstract
from core.src.world.repositories import RepositoriesFactory
from core.src.world.types import Pos, Direction


class Character(CharacterAbstract):
    def __init__(self):
        self._character_id = None
        self._pos = None
        self._name = None
        self._stales = set()
        self._channel_id = None

    @staticmethod
    def _get_repo_factory(repo):
        if not repo:
            from core.src.world.builder import repositories
            return repositories
        return repo

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def character_id(self) -> str:
        return self._character_id

    def set_channel(self, channel_id: str):
        self._channel_id = channel_id

    @property
    def pos(self):
        return self._pos

    def set_pos(self, pos: Pos) -> 'Character':
        self._pos = pos
        return self

    def set_id(self, character_id: str) -> 'Character':
        self._character_id = character_id
        return self

    def set_name(self, name: str) -> 'Character':
        self._name = name
        return self

    @classmethod
    def from_dict(cls, values: typing.Dict) -> 'Character':
        instance = cls()
        for k, v in values.items():
            setattr(instance, '_' + k, v)
        return instance

    @classmethod
    def new(cls, character_id: str, name: str) -> 'Character':
        instance = cls().set_name(name).set_id(character_id)
        return instance

    @classmethod
    def login(cls, character_id: str, repo: typing.Optional[RepositoriesFactory]=None):
        repo = cls._get_repo_factory(repo)
        data = repo.character.get(character_id)
        instance = cls().set_id(character_id).set_name(data['name'])
        instance.set_channel(repo.world.login(character_id)).set_pos(repo.world.get_pos(character_id))
        return instance

    def logout(self, repo: typing.Optional[RepositoriesFactory]=None):
        repo = self._get_repo_factory(repo)
        repo.world.logout(self.character_id)
        return self

    def look(self, direction: Direction):
        raise NotImplementedError
