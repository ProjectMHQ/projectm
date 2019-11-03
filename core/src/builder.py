from redis import StrictRedis

from core.src.repositories.redis_characters_repository import RedisCharactersRepositoryImpl
from core.src.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.repositories.sql_characters_repository import SQLCharactersRepositoryImpl
from etc import settings
from core.src import database
from core.src.repositories.users_repository import UsersRepositoryImpl
from core.src.services.authentication import AuthenticationServiceImpl
from core.src.services.encryption import AESCipherServiceImpl

if settings.RUNNING_TESTS:
    from unittest.mock import Mock
    strict_redis = Mock()
else:
    strict_redis = StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB
    )

encryption_service = AESCipherServiceImpl(
    key=settings.ENCRYPTION_KEY,
    iv=settings.ENCRYPTION_IV
)
psql_character_repository = SQLCharactersRepositoryImpl(database.db)
user_repository = UsersRepositoryImpl(database.db)
auth_service = AuthenticationServiceImpl(encryption_service, user_repository)

redis_characters_index_repository = RedisCharactersRepositoryImpl(strict_redis)
ws_channels_repository = WebsocketChannelsRepository(strict_redis)
