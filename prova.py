import time

import os
from redis import StrictRedis
from etc import settings


redis = StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
)

if __name__ == '__main__':
    #script = """
    #local val=redis.call('bitpos', 'eee', 0)
    #redis.call('setbit', 'eee', val, 1)
    #local key = string.format('e%s', val)
    #redis.call('hmset', key, 'status', 'redispower')
    #return val
    #"""
    #x = redis.eval(script, 0)
    #print(redis.hmget('e' + str(x), 'status'))

    now = int(time.time())
    script = """
        local val=redis.call('bitpos', 'e:idmap', 0)
        redis.call('setbit', 'e:id', val, 1)
        local key = string.format('e:%s', val)
        redis.call('hmset', key, 'created_at', ARGV[1])
        return val
        """
    x = redis.eval(script, 0, now)
    print(redis.hmget('e:' + str(x), 'created_at'))
