from redis import StrictRedis


class RedisCharactersRepositoryImpl:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'char:e'

    def get_entity_id(self, character_id: str):
        return self.redis.hget(self.prefix, character_id)

    def set_entity_id(self, character_id: str, entity_id: str):
        assert not self.redis.hget(self.prefix, character_id)
        return self.redis.hmset(self.prefix, {character_id: entity_id})
