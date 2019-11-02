from etc import settings
from redis import StrictRedis

"""
this module is intended to setup redis before the service execution.

please set here all the redis instructions needed for a proper system setup. 
"""

redis = StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)

if __name__ == '__main__':
    redis.setbit('e:idmap', 0, 1)
