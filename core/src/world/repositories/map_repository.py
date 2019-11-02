from redis import StrictRedis


class MapRepository:
    def __init__(self, redis: StrictRedis):
        self.redis = redis
        self.prefix = 'm'
        self.entities_prefix = 'e'

    def get_entity_position(self, entity_id: int):
        raise NotImplementedError
