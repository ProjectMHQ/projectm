import hashlib
import time
import typing
import sqlalchemy
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from core.src import exceptions
from core.src.business.user.types import UserStatus
from core.src.database import Base, json_column_type


class Character(Base):
    __tablename__ = 'character'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    character_id = sqlalchemy.Column(sqlalchemy.String(36), nullable=False, unique=True, index=True)
    name = sqlalchemy.Column(sqlalchemy.String(32), nullable=False, unique=True, index=True)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now())
    updated_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=True, onupdate=sqlalchemy.func.now())
    version_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=1, server_default='1')
    meta = sqlalchemy.Column(
        json_column_type,
        unique=False,
        nullable=False,
    )

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", backref="characters")
