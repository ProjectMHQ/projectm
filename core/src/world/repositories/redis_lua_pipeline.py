import binascii
import os


class RedisLUAPipeline:
    """
    A "Value Bounded" pipeline reimplementation of the Redis Pipeline component.
    It produces a LUA script to use a Pipeline while adding conditions to be verified before the execution.
    Something like a SELECT FOR UPDATE.
    """
    def __init__(self, redis):
        self.value = ""
        self.redis = redis

    def allocate_value(self, key='value'):
        self.value += "local {} = ".format(key)
        return self

    def add_if_equal(self, expected_value, value_name='value', value_selector=""):
        if isinstance(expected_value, int):
            expected_value = expected_value
            self.value += "if {}{} ~= {} then\nreturn 0\nend\n".format(value_name, value_selector, expected_value)
        elif isinstance(expected_value, str):
            self.value += "if {}{} ~= '{}' then\nreturn 0\nend\n".format(value_name, value_selector, expected_value)
        elif isinstance(expected_value, list):
            lua_table = '{' + ', '.join([str(x) for x in expected_value]) + '}'
            self.value += "if table.concat({}{}) ~= table.concat({}) then\nreturn 0\nend\n".format(
                value_selector, value_name, lua_table
            )
        return self

    def hget(self, key, value):
        self.value += "redis.call('hget', '{}', '{}')\n".format(key, value)

    def setbit(self, key, bit, value):
        self.value += "redis.call('setbit', '{}', {}, {})\n".format(key, bit, value)

    def zadd(self, key, *payload):
        ppload = ", ".join(["'{}'".format(str(p)) for p in payload])
        self.value += "redis.call('zadd', '{}', {})\n".format(key, ppload)

    def zrem(self, key, *payload):
        ppload = ", ".join(["'{}'".format(str(p)) for p in payload])
        self.value += "redis.call('zrem', '{}', {})\n".format(key, ppload)

    def hset(self, key, subkey, value):
        self.value += "redis.call('hset', '{}', '{}', '{}')\n".format(key, subkey, value)

    def hincrby(self, key, subkey, value):
        self.value += "redis.call('hincrby', '{}', '{}', {})\n".format(key, subkey, value)

    def hmset_dict(self, key, value):
        values = ""
        for k, v in value.items():
            values += "'{}', '{}',".format(k, v)
        values = values.rstrip(',')
        self.value += "redis.call('hmset', '{}', {})\n".format(key, values)

    def hdel(self, key, *values):
        value = ', '.join(["'{}'".format(str(v)) for v in values])
        self.value += "redis.call('hdel', '{}', {})\n".format(key, value)

    def zscan(self, key, cursor=0, match=None):
        assert all((key, match)), (key, cursor, match)
        self.value += "redis.call('zscan', '{}', {}, 'match', '{}')\n".format(key, cursor, match)

    def zrange(self, key, min_value, max_value):
        self.value += "redis.call('zrange', '{}', {}, {})\n".format(key, min_value, max_value)

    def zprepareinter(self, key, values_to_inter):
        seed = binascii.hexlify(os.urandom(8)).decode()
        values = ', '.join(["0, '{}'".format(value) for value in values_to_inter])
        self.value += "redis.call('zadd', 'temp:{}:1', {})\n".format(seed, values)
        self.value += "redis.call('zinterstore', 'temp:{0}:2', 2, '{1}', 'temp:{0}:1')\n".format(seed, key)
        return seed

    def zfetchinter(self, seed):
        self.value += "redis.call('zrange', 'temp:{}:2', 0, -1)\n".format(seed)
        self.value += "redis.call('del', 'temp:{0}:2', 'temp:{0}:1')\n".format(seed)

    def return_exit(self, value_key=None):
        self.value += "return {}".format(value_key or 0)

    async def execute(self, return_value_at_exit=1):
        self.return_exit(value_key=return_value_at_exit)
        return await self.redis.eval(self.value)