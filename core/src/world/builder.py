from core.src.builder import strict_redis
from core.src.world.repositories.data_repository import EntitiesRepository


world_repository = EntitiesRepository(strict_redis)
world_map_repository = NotImplementedError
