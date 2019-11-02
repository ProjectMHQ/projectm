import time

from redis import StrictRedis

from core.src.world.domain.components.connection import Components
from etc import settings

exit()

connections = [
    StrictRedis(
    host='removeme' + settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB
) for _ in range(0, 30)]


bla = 'DONTRUNME!'


def create_entity(connection):
    script = """
        local val=redis.call('bitpos', '{0}:idmap', 0)
        redis.call('setbit', '{0}:idmap', val, 1)
        local key = string.format('{0}:%s', val)
        redis.call('hmset', key, '{1}', ARGV[1])
        return val
        """.format(bla, Components.base.CREATED_AT.value)
    return connections[connection % 30].eval(script, 0, int(time.time()))


from multiprocessing import Pool as ThreadPool


s = time.time()
pool = ThreadPool(30)
results = []
pool.map(create_entity, range(0, 100000))

pool.close()
pool.join()
print(connections[0].bitpos('{}:idmap'.format(bla), 0))
print(time.time() - s)
