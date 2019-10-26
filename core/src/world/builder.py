from redis import StrictRedis
from core.src.world.repositories import RepositoriesFactory
from core.src.world.repositories.character_repository import RedisCharacterRepositoryImpl
from core.src.world.repositories.world_repository import RedisWorldRepositoryImpl
from etc import settings


_redis = StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)

repositories = RepositoriesFactory(
    world=RedisWorldRepositoryImpl(_redis),
    character=RedisCharacterRepositoryImpl(_redis)
)
