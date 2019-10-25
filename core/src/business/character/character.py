import enum
import typing

from core.src.business.character.abstract import CharacterDOAbstract


class CharacterDOImpl(CharacterDOAbstract):
    def __init__(
        self,
        character_id=None,
        name=None,
        pos=None,
        meta=None,
        user_id=None
    ):
        self._character_id = character_id
        self._name = name
        self._pos = pos
        self._meta = meta
        self._user_id = user_id

    @staticmethod
    def _get_characters_repository(repository):
        if repository:
            return repository
        from core.src.builder import character_repository
        return character_repository

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def character_id(self) -> str:
        return self._character_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def pos(self) -> typing.Tuple:
        return self._pos

    @classmethod
    def from_model(cls, model):
        instance = cls(
            character_id=model.character_id,
            name=model.name,
            meta=model.meta,
            user_id=model.user.user_id
        )
        return instance

    def as_dict(self, context=None):
        return {
            "character_id": self.character_id,
            "name": self.name,
            "pos": self.pos and list(self.pos),
        }

    def ensure_can_authenticate(self, repo=None):
        # repo = self._get_characters_repository(repo)
        # TODO
        # characters_statuses = repo.get_all_characters_login_status(user_id=self.user_id)
        # Block multiple logins
        # Issue: https://github.com/gdassori/projectm/issues/14
        return True

    @classmethod
    def from_session_token(cls, token: typing.Dict):
        instance = cls(character_id=token['character_id'])
        return instance
