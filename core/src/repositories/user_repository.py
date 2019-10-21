import itertools
import typing
import uuid

from sqlalchemy.orm import scoped_session, Session

from etc import settings
from core.src import models
from core.src.business.user.types import UserStatus
from core.src.database import atomic


class UserRepositoryImpl:
    def __init__(self, session_factory: scoped_session):
        self._session_factory = session_factory

    @staticmethod
    def _get_new_users_default_roles():
        return ['admin']

    @staticmethod
    def _get_new_users_default_status():
        if settings.EMAIL_MUST_BE_CONFIRMED:
            return UserStatus.LOCKED.value
        else:
            return UserStatus.ACTIVE.value

    @staticmethod
    def _get_random_uuid():
        return str(uuid.uuid4())

    @property
    def session(self) -> Session:
        return self._session_factory()

    def get_user_by_field(self, field_name: str, field_value: typing.Any) -> models.User:
        return self.session.query(models.User).filter(getattr(models.User, field_name) == field_value).one()

    def get_multiple_users_by_field(self, field_name: str, field_value: typing.Any) -> typing.List[models.User]:
        return self.session.query(models.User).filter(getattr(models.User, field_name) == field_value)

    @atomic
    def create_user(self, email: str, password: str):
        user = models.User(
            email=email,
            user_id=self._get_random_uuid(),
            status=self._get_new_users_default_status(),
        )
        user.roles = self._get_new_users_default_roles()
        user.set_password(password)
        self.session.add(user)
        self.session.flush()
        return user

    @atomic
    def update_user(self, user: models.User, data: typing.Dict = None):
        if data:
            for k, v in data.items():
                if v is not None and getattr(user, k, None) != v:
                    if k == 'password':
                        user.set_password(v)
                    elif k == 'roles':
                        user.roles = v
                    elif k == 'meta':
                        user.meta = {k: v for k, v in itertools.chain(user.meta.items(), v.items())}
                    else:
                        setattr(user, k, v)
        self.session.add(user)
        self.session.flush()
        return user
