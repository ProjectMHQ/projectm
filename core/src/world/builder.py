import aioredis
from etc import settings
from core.src.builder import strict_redis
from core.src.world.repositories.data_repository import RedisDataRepository


world_repository = RedisDataRepository(strict_redis)


async def redis_pool():
    return await aioredis.create_redis_pool(
        'redis://{}:{}'.format(
            settings.REDIS_HOST,
            settings.REDIS_PORT
        ),
        db=settings.REDIS_DB,
        maxsize=64
    )
