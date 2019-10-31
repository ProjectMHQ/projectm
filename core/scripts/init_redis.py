from etc import settings
from redis import StrictRedis

redis = StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)

if __name__ == '__main__':
    redis.setbit('e:idmap', 0, 1)
