import time
from redis import StrictRedis

from core.src.business.character import exceptions
from core.src.business.character.abstract import CharacterServiceAbstract, CharacterDOAbstract
from core.src.services.redis_service import RedisServiceBase


class CharacterServiceImpl(CharacterServiceAbstract, RedisServiceBase):
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'ch/'

    def exists(self, character: CharacterDOAbstract):
        return bool(self.redis.exists(self.prefix + character.character_id))

    def get_coordinates(self, character: CharacterDOAbstract):
        return [0, 0]

    def allocate_character(self, character: CharacterDOAbstract):
        # FIXME session_id ?
        login_template = {
            'logged_in_at': int(time.time()),
            'user_id': character.user_id,
            'name': character.name
        }
        if self.exists(character):
            raise exceptions.CharacterAlreadyAllocated
        self.redis.set(self.prefix + character.character_id, self._json_to_redis(login_template))

    def drop_character(self, character: CharacterDOAbstract):
        if not self.exists(character):
            raise exceptions.CharacterNotAllocated
        self.redis.delete(self.prefix + character.character_id)
