import hashlib
import time
import typing
import sqlalchemy
from core.src import exceptions
from core.src.business.user.types import UserStatus
from core.src.database import Base, json_column_type


class User(Base):
    __tablename__ = 'user'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.String(36), nullable=False, unique=True, index=True)
    status = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, unique=False, index=True)
    full_name = sqlalchemy.Column(sqlalchemy.String(32), nullable=True, unique=True, index=True)
    email = sqlalchemy.Column(sqlalchemy.String(256), nullable=False, unique=True, index=True)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now())
    updated_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=True, onupdate=sqlalchemy.func.now())
    version_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=1, server_default='1')
    hashed_password = sqlalchemy.Column(sqlalchemy.String(36), nullable=False, unique=False, index=True)
    __mapper_args__ = {
        "version_id_col": version_id
    }
    meta = sqlalchemy.Column(
        json_column_type,
        unique=False,
        nullable=False,
    )

    @property
    def roles(self):
        return self.meta.get('roles', [])

    @roles.setter
    def roles(self, value):
        assert isinstance(value, list)
        if self.meta is None:
            self.meta = {'roles': value}
        else:
            self.meta['roles'] = value

    @staticmethod
    def _get_hashed_password(password):
        nonce = int(1024 / len(password))
        for x in range(0, 1024*16 + nonce):
            password = hashlib.sha256(password.encode()).hexdigest()
        return password

    def validate_password(self, password: str):
        password = self._get_hashed_password(password)
        if self.hashed_password != password:
            raise exceptions.InvalidPasswordException

    def set_password(self, password: str):
        self.hashed_password = self._get_hashed_password(password)

    def as_dict(self, context=None):
        return {
            'user_id': self.user_id,
            'full_name': self.full_name,
            'email': self.email,
            'status': UserStatus(self.status).name,
            'roles': self.roles,
            'created_at': self.created_at and self.created_at.isoformat()
        }

    def mark_activation_email_as_sent(self):
        self.meta['activation_email_sent_at'] = int(time.time())
        self.status = UserStatus.EMAIL_CONFIRMATION_PENDING.value
        return self

    @property
    def activation_email_sent_at(self) -> typing.Optional[int]:
        return self.meta.get('activation_email_sent_at')

    def mark_email_as_confirmed(self):
        self.meta['email_confirmed_at'] = int(time.time())
        return self

    def set_user_as_active(self):
        self.status = UserStatus.ACTIVE.value
        return self

    @property
    def email_confirmed_at(self) -> typing.Optional[int]:
        return self.meta.get('email_confirmed_at')
