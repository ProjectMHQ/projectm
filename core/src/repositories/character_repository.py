import itertools
import typing
import uuid

from sqlalchemy.orm import scoped_session, Session

from core.src import models
from core.src.business.character.abstract import CharacterDOAbstract
from core.src.business.user.abstract import UserDOAbstract
from core.src.database import atomic


class CharacterRepositoryImpl:
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
        from core.src.business.character.character import CharacterDOImpl
        query = self.session.query(models.Character).filter(getattr(models.Character, field_name) == field_value)
        if user_id:
            query = query.join(models.User).filter(models.User.user_id == user_id)
        res = query.one()
        return CharacterDOImpl.from_model(res)

    def get_multiple_characters_by_field(self, field_name: str, field_value: typing.Any) \
            -> typing.List[CharacterDOAbstract]:
        if field_name == 'user_do':
            field_name = 'user'
            field_value = self.session.query(models.User).filter(models.User.user_id == field_value.user_id).one()
        from core.src.business.character.character import CharacterDOImpl
        return [
            CharacterDOImpl.from_model(c) for c in
            self.session.query(models.Character).filter(getattr(models.Character, field_name) == field_value)
        ]

    @atomic
    def create_character(
            self,
            user: UserDOAbstract,
            name: str
    ) -> CharacterDOAbstract:
        character = models.Character(
            user=self.session.query(models.User).filter(models.User.user_id == user.user_id).one(),
            character_id=self._get_random_uuid(),
            name=name
        )
        self.session.add(character)
        self.session.flush()
        from core.src.business.character.character import CharacterDOImpl
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
