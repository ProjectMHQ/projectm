import json
import time
import typing

from etc import settings
from core.src import exceptions, models
from core.src.business.user.types import UserStatus
from core.src.database import atomic
from core.src.logging_factory import LOGGING_FACTORY
from core.src.services.abstracts import AuthenticationServiceAbstract


class AuthenticationServiceImpl(AuthenticationServiceAbstract):
    def __init__(self, encryption_service, user_repository):
        self.encryption_service = encryption_service
        self.user_repository = user_repository

    def _get_login_token(self, user_data: typing.Dict) -> typing.AnyStr:
        token = {
            'user': user_data,
            'created_at': int(time.time()),
            'ttl': settings.TOKEN_TTL,
        }
        payload = json.dumps(token)
        return self.encryption_service.encrypt(payload)

    def _get_websocket_token(self, data: typing.Dict) -> typing.AnyStr:
        token = {
            'context': 'world',
            'data': data,
            'created_at': int(time.time()),
            'ttl': settings.TOKEN_TTL,
        }
        payload = json.dumps(token)
        return self.encryption_service.encrypt(payload)

    @atomic
    def signup(
            self,
            email: typing.AnyStr,
            password: typing.AnyStr
    ):
        user = self.user_repository.create_user(email, password)
        return user.as_dict()

    @atomic
    def update_user(self, user: models.User, data: typing.Dict):
        user = self.user_repository.update_user(user, data=data)
        return user.as_dict()

    def login(self, email: typing.AnyStr, password: typing.AnyStr) -> typing.Dict:
        user = self.user_repository.get_user_by_field('email', email)
        if user.status != UserStatus.ACTIVE:
            raise exceptions.UnauthorizedError(
                message='USER_NOT_ACTIVE',
                status_code=401
            )
        user.validate_password(password)
        return {
            "user_id": user.user_id,
            "token": self._get_login_token(user.as_dict(context='token')),
            "expires_at": settings.TOKEN_TTL + int(time.time())
        }

    def logout(self, *a, **kw):
        LOGGING_FACTORY.core.info('Logout: %s', ', '.join(a))

    def decode_session_token(self, session_token: typing.AnyStr) -> typing.Dict:
        LOGGING_FACTORY.core.debug('Decoding session token: %s', session_token)
        now = int(time.time())
        token = json.loads(self.encryption_service.decrypt(session_token))
        LOGGING_FACTORY.core.debug('Decoding session token: %s - %s', session_token, token)
        expires_at = token['ttl'] + token['created_at']
        if expires_at < now:
            raise exceptions.SessionExpiredException
        return token

    @atomic
    def confirm_email_address(self, email_token: str):
        data = json.loads(self.encryption_service.decrypt(email_token))
        expires_at = data['ttl'] + data['created_at']
        now = int(time.time())
        if expires_at < now:
            raise exceptions.EmailConfirmationTokenExpiredException
        user = self.user_repository.get_user_by_field('email', data['email'])
        user = user.mark_email_as_confirmed().set_user_as_active()
        return self.user_repository.update_user(user)

    @atomic
    def authenticate_character(self, character_data: typing.Dict) -> typing.Dict:
        return {
            "character_id": character_data['character_id'],
            "token": self._get_websocket_token(character_data),
            "expires_at": settings.TOKEN_TTL + int(time.time())
        }
