import itertools
import typing
import uuid

from sqlalchemy.orm import scoped_session, Session

from core.src.auth import models
from core.src.auth.business.character.abstract import CharacterDOAbstract

from core.src.auth.database import atomic


class SQLCharactersRepositoryImpl:
    def __init__(self, session_factory: scoped_session):
        self._session_factory = session_factory

    @staticmethod
    def _get_random_uuid() -> str:
        return str(uuid.uuid4())

    @property
    def session(self) -> Session:
        return self._session_factory()

    def get_character_by_field(
            self, field_name: str, field_value: typing.Any, user_id: typing.Optional[str]=None
    ) -> CharacterDOAbstract:
        query = self.session.query(models.Character).filter(getattr(models.Character, field_name) == field_value)
        if user_id:
            query = query.join(models.User).filter(models.User.user_id == user_id)
        res = query.one()
        from core.src.auth.business.character.character import CharacterDOImpl
        return CharacterDOImpl.from_model(res)

    def get_multiple_characters_by_field(self, field_name: str, field_value: typing.Any) \
            -> typing.List[CharacterDOAbstract]:
        if field_name == 'user_do':
            field_name = 'user'
            field_value = self.session.query(models.User).filter(models.User.user_id == field_value.user_id).one()
        from core.src.auth.business.character.character import CharacterDOImpl
        return [
            CharacterDOImpl.from_model(c) for c in
            self.session.query(models.Character).filter(getattr(models.Character, field_name) == field_value)
        ]

    @atomic
    def store_new_character(
            self,
            user_id: str,
            name: str
    ) -> CharacterDOAbstract:
        character = models.Character(
            user=self.session.query(models.User).filter(models.User.user_id == user_id).one(),
            character_id=self._get_random_uuid(),
            name=name,
            meta={}
        )
        self.session.add(character)
        self.session.flush()
        from core.src.auth.business.character.character import CharacterDOImpl
        return CharacterDOImpl.from_model(character)

    @atomic
    def update_character(self, character: models.Character, data: typing.Dict = None) -> models.Character:
        if data:
            for k, v in data.items():
                if v is not None and getattr(character, k, None) != v:
                    if k == 'meta':
                        character.meta = {k: v for k, v in itertools.chain(character.meta.items(), v.items())}
                    else:
                        setattr(character, k, v)
        self.session.add(character)
        self.session.flush()
        return character
