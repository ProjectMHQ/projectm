import itertools
import typing
import uuid

from sqlalchemy.orm import scoped_session, Session

from core.src import models
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

    def get_character_by_field(self, field_name: str, field_value: typing.Any) -> models.Character:
        return self.session.query(models.Character).filter(getattr(models.Character, field_name) == field_value).one()

    def get_multiple_characters_by_field(self, field_name: str, field_value: typing.Any) -> typing.List[models.Character]:
        return self.session.query(models.Character).filter(getattr(models.Character, field_name) == field_value)

    @atomic
    def create_character(
            self, user: models.User,
            name: str
    ) -> models.Character:
        character = models.Character(
            user=user,
            character_id=self._get_random_uuid(),
            name=name
        )
        self.session.add(character)
        self.session.flush()
        return character

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
