from core.src.builder import strict_redis
from core.src.world.repositories.data_repository import RedisDataRepository


world_repository = RedisDataRepository(strict_redis)
world_map_repository = NotImplementedError
