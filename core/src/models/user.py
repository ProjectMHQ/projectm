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
    hashed_password = sqlalchemy.Column(sqlalchemy.String(64), nullable=False, unique=False, index=True)
    __mapper_args__ = {
        "version_id_col": version_id
    }
    meta = sqlalchemy.Column(
        json_column_type,
        unique=False,
        nullable=False,
    )
