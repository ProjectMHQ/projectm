import enum
from etc import settings
import aioredis


class RedisType(enum.IntEnum):
    DATA = 0
    QUEUES = 1


connection_pools = {}


def get_redis_factory(rtype: RedisType):

    if settings.INTEGRATION_TESTS:
        endpoint = 'redis://{}:{}/{}'.format(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_TEST_DB)
    else:
        if rtype == RedisType.DATA:
            endpoint = 'redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT)
        elif rtype == RedisType.QUEUES:
            endpoint = 'redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT)
        else:
            raise ValueError('wtf?')

    async def async_redis_pool_factory(max_size=1024):
        if not connection_pools.get(rtype):
            connection_pool = await aioredis.create_redis_pool(
                endpoint,
                db=settings.REDIS_DB,
                maxsize=max_size
            )
            connection_pools[rtype] = connection_pool
        return connection_pools[rtype]

    return async_redis_pool_factory
