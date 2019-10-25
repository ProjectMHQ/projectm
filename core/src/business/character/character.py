import enum
import typing

from core.src.business.character.abstract import CharacterDOAbstract


FIRST_COORDINATES = (0, 0)


class CharacterGender(enum.Enum):
    MALE = 0
    FEMALE = 1


class CharacterRace(enum.Enum):
    HUMAN = 0


class CharacterDOImpl(CharacterDOAbstract):
    def __init__(
        self,
        character_id=None,
        name=None,
        at_coordinates=None,
        meta=None,
        user_id=None
    ):
        self._character_id = character_id
        self._name = name
        self._at_coordinates = at_coordinates
        self._meta = meta or {
            'gender': 0,
            'race': 0  # TODO FIXME
        }
        self._user_id = user_id

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
    def gender(self) -> CharacterGender:
        return self._meta['gender']

    @property
    def at_coordinates(self) -> typing.Tuple:
        return self._at_coordinates

    @property
    def race(self) -> enum.Enum:
        return self._meta['race']

    @classmethod
    def from_model(cls, model):
        instance = cls(
            character_id=model.character_id,
            name=model.name,
            at_coordinates=FIRST_COORDINATES,
            meta=model.meta,
            user_id=model.user.user_id
        )
        return instance

    def as_dict(self, context=None):
        return {
            "character_id": self.character_id,
            "name": self.name,
            "at_coordinates": list(self.at_coordinates),
        }
