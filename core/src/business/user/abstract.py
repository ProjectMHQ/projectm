import abc
import typing


class UserDOAbstract(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def email(self):
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def user_id(self):
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def status(self):
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def full_name(self):
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def hashed_password(self):
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def created_at(self):
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def updated_at(self):
        pass  # pragma: no cover

    @classmethod
    @abc.abstractmethod
    def from_model(cls, model):
        pass  # pragma: no cover

    @abc.abstractmethod
    def as_dict(self, context=None):
        pass  # pragma: no cover

    @abc.abstractmethod
    def mark_activation_email_as_sent(self):
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def activation_email_sent_at(self) -> typing.Optional[int]:
        pass  # pragma: no cover

    @abc.abstractmethod
    def mark_email_as_confirmed(self):
        pass  # pragma: no cover

    @abc.abstractmethod
    def set_user_as_active(self):
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def email_confirmed_at(self) -> typing.Optional[int]:
        pass  # pragma: no cover

    @abc.abstractmethod
    def validate_password(self, password: str):
        pass  # pragma: no cover

    @abc.abstractmethod
    def set_password(self, password: str):
        pass  # pragma: no cover
