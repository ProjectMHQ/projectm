from redis import StrictRedis

from core.src.auth.repositories.redis_characters_repository import RedisCharactersRepositoryImpl
from core.src.auth.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.auth.repositories.sql_characters_repository import SQLCharactersRepositoryImpl
from core.src.auth.repositories.users_repository import UsersRepositoryImpl
from etc import settings
from core.src.auth import database
from core.src.auth.services.authentication import AuthenticationServiceImpl
from core.src.auth.services.encryption import AESCipherServiceImpl

if settings.RUNNING_TESTS and not settings.INTEGRATION_TESTS:
    from unittest.mock import Mock
    strict_redis = Mock()
else:
    if settings.INTEGRATION_TESTS:
        redis_db = settings.REDIS_TEST_DB
    else:
        redis_db = settings.REDIS_DB

    strict_redis = StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=redis_db
    )

encryption_service = AESCipherServiceImpl(
    key=settings.ENCRYPTION_KEY,
    iv=settings.ENCRYPTION_IV
)
if settings.RUNNING_TESTS and settings.INTEGRATION_TESTS:
    from unittest.mock import Mock
    psql_character_repository = Mock()
else:
    psql_character_repository = SQLCharactersRepositoryImpl(database.db)

user_repository = UsersRepositoryImpl(database.db)
auth_service = AuthenticationServiceImpl(encryption_service, user_repository)

redis_characters_index_repository = RedisCharactersRepositoryImpl(strict_redis)
ws_channels_repository = WebsocketChannelsRepository(strict_redis)
