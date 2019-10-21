from enum import Enum


class UserStatus(Enum):
    LOCKED = 1
    ACTIVE = 2
    EMAIL_CONFIRMATION_PENDING = 3
