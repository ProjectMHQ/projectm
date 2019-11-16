from etc import settings
import aioredis


async def async_redis_pool_factory(max_size=128):
    return await aioredis.create_redis_pool(
        'redis://{}:{}'.format(
            settings.REDIS_HOST,
            settings.REDIS_PORT
        ),
        db=settings.REDIS_DB,
        maxsize=max_size
    )
