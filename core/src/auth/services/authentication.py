import json
import time
import typing

from core.src.auth.business.user.types import UserStatus
from etc import settings
from core.src.auth import models, exceptions
from core.src.auth.database import atomic
from core.src.auth.logging_factory import LOGGER
from core.src.auth.services.abstracts import AuthenticationServiceAbstract


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

    def _get_websocket_token(self, context, **data) -> typing.AnyStr:
        token = {
            'context': context,
            'created_at': int(time.time()),
            'ttl': settings.TOKEN_TTL,
        }
        if data:
            token['data'] = data
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
                description='USER_NOT_ACTIVE',
                code=401
            )
        user.validate_password(password)
        return {
            "user_id": user.user_id,
            "token": self._get_login_token(user.as_dict(context='token')),
            "expires_at": settings.TOKEN_TTL + int(time.time())
        }

    def logout(self, *a, **kw):
        LOGGER.core.info('Logout: %s', ', '.join(a))

    def decode_session_token(self, session_token: typing.AnyStr) -> typing.Dict:
        LOGGER.core.debug('Decoding session token: %s', session_token)
        now = int(time.time())
        token = json.loads(self.encryption_service.decrypt(session_token))
        LOGGER.core.debug('Decoding session token: %s', token)
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
    def get_token_for_new_character(self, user_id: str) -> typing.Dict:
        return {
            "token": self._get_websocket_token('world:create', user_id=user_id),
            "expires_at": settings.TOKEN_TTL + int(time.time())
        }

    @atomic
    def get_token_for_existing_character(self, character_id: str) -> typing.Dict:
        return {
            "token": self._get_websocket_token('world:auth', character_id=character_id),
            "expires_at": settings.TOKEN_TTL + int(time.time())
        }
