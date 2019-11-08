import itertools
import typing
import uuid

from sqlalchemy.orm import scoped_session, Session

from core.src.auth import models, exceptions
from core.src.auth.business.user.abstract import UserDOAbstract
from core.src.auth.database import atomic


class UsersRepositoryImpl:
    def __init__(self, session_factory: scoped_session):
        self._session_factory = session_factory

    @staticmethod
    def _get_random_uuid() -> str:
        return str(uuid.uuid4())

    @property
    def session(self) -> Session:
        return self._session_factory()

    def get_user_by_field(self, field_name: str, field_value: typing.Any) -> UserDOAbstract:
        model = self.session.query(models.User).filter(getattr(models.User, field_name) == field_value).one()
        from core.src.auth.business.user.user import UserDOImpl
        return UserDOImpl.from_model(model)

    def get_multiple_users_by_field(self, field_name: str, field_value: typing.Any) -> typing.List[UserDOAbstract]:
        from core.src.auth.business.user.user import UserDOImpl
        return [
            UserDOImpl.from_model(x)
            for x in self.session.query(models.User).filter(getattr(models.User, field_name) == field_value)
        ]

    @atomic
    def create_user(self, email: str, password: str) -> UserDOAbstract:
        from core.src.auth.business.user.user import UserDOImpl
        user = UserDOImpl(email=email).set_password(password)
        model = models.User(
            email=user.email,
            user_id=self._get_random_uuid(),
            status=user.status.value,
            hashed_password=user.hashed_password,
            meta=user.meta
        )
        try:
            self.session.add(model)
            self.session.flush()
        except Exception as e:
            if 'UNIQUE' in str(e.args[0]):
                raise exceptions.ResourceDuplicated(e.args[0])
            raise e
        user._user_id = model.user_id
        return user

    @atomic
    def update_user(self, user: models.User, data: typing.Dict = None) -> UserDOAbstract:
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
