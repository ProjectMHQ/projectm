import hashlib

import time
import typing

from core.src.auth import exceptions
from core.src.auth.business.character import CharacterDOAbstract
from core.src.auth.business import UserDOAbstract
from core.src.auth.business import UserStatus


class UserDOImpl(UserDOAbstract):
    def __init__(
            self,
            email=None,
            user_id=None,
            status=None,
            full_name=None,
            created_at=None,
            updated_at=None,
            meta=None,
            hashed_password=None,
    ):
        self._email = email
        self._user_id = user_id
        self._status = status or self._get_new_users_default_status()
        self._full_name = full_name
        self._created_at = created_at
        self._updated_at = updated_at
        self._meta = meta or {'roles': []}
        self._hashed_password = hashed_password

    @staticmethod
    def _get_new_users_default_status():
        from etc import settings
        if settings.EMAIL_MUST_BE_CONFIRMED:
            return UserStatus.LOCKED
        else:
            return UserStatus.ACTIVE

    @staticmethod
    def _get_repository(repository):
        if repository:
            return repository
        from core.src.auth.builder import user_repository
        return user_repository

    @staticmethod
    def _get_characters_repository(repository):
        if repository:
            return repository
        from core.src.auth.builder import psql_character_repository
        return psql_character_repository

    @classmethod
    def get_by_user_id(cls, user_id: str, repository=None):
        repository = cls._get_repository(repository)
        return repository.get_user_by_field('user_id', user_id)

    @classmethod
    def get_by_email(cls, email: str, repository=None):
        repository = cls._get_repository(repository)
        return repository.get_user_by_field('user_id', email)

    @property
    def email(self):
        return self._email

    @property
    def user_id(self):
        return self._user_id
    
    @property
    def status(self):
        return self._status

    @property
    def meta(self):
        return self._meta

    @property
    def full_name(self):
        return self._full_name

    @property
    def hashed_password(self):
        return self._hashed_password

    @property
    def created_at(self):
        return self._created_at
    
    @property
    def updated_at(self):
        return self._updated_at

    @property
    def roles(self):
        return self._meta.get('roles')

    @classmethod
    def from_model(cls, model):
        instance = cls(
            email=model.email,
            user_id=model.user_id,
            status=UserStatus(model.status),
            full_name=model.full_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
            hashed_password=model.hashed_password
        )
        return instance

    @roles.setter
    def roles(self, value):
        assert isinstance(value, list)
        if self._meta is None:
            self._meta = {'roles': value}
        else:
            self._meta['roles'] = value

    @staticmethod
    def _get_hashed_password(password):
        nonce = int(1024 / len(password))
        for x in range(0, 1024*16 + nonce):
            password = hashlib.sha256(password.encode()).hexdigest()
        return password

    def validate_password(self, password: str):
        password = self._get_hashed_password(password)
        if self._hashed_password != password:
            raise exceptions.InvalidPasswordException
        return self

    def set_password(self, password: str):
        self._hashed_password = self._get_hashed_password(password)
        return self

    def as_dict(self, context=None):
        if context == 'token':
            return {
                'user_id': self.user_id,
                'status': UserStatus(self.status).name,
                'roles': self.roles
            }
        return {
            'user_id': self.user_id,
            'full_name': self.full_name,
            'email': self.email,
            'status': UserStatus(self.status).name,
            'roles': self.roles,
            'created_at': self.created_at and self.created_at.isoformat()
        }

    def mark_activation_email_as_sent(self):
        self._meta['activation_email_sent_at'] = int(time.time())
        self._status = UserStatus.EMAIL_CONFIRMATION_PENDING
        return self

    @property
    def activation_email_sent_at(self) -> typing.Optional[int]:
        return self._meta.get('activation_email_sent_at')

    def mark_email_as_confirmed(self):
        self._meta['email_confirmed_at'] = int(time.time())
        return self

    def set_user_as_active(self):
        self._status = UserStatus.ACTIVE
        return self

    @property
    def email_confirmed_at(self) -> typing.Optional[int]:
        return self._meta.get('email_confirmed_at')

    def get_characters(self, repository=None) -> typing.List[CharacterDOAbstract]:
        repository = self._get_characters_repository(repository)
        return repository.get_multiple_characters_by_field('user_do', self)

