import typing
import uuid
from redis import StrictRedis


class RedisWorldRepositoryImpl:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'wd/'

    def get_character_pos(self, character_id: str):
        return self.redis.hmget(self.prefix + 'pos', character_id)

    def login(self, character_id: str) -> str:
        channel_id = str(uuid.uuid4())
        self.redis.hmset(self.prefix + 'chan', {character_id: channel_id})
        return channel_id

    def logout(self, character_id: str):
        return self.redis.hdel(self.prefix + 'chan', character_id)

    def allocate(self, character_id: str, pos: str) -> bool:
        self.redis.hmset(self.prefix + 'pos', {character_id: pos})
        return True
