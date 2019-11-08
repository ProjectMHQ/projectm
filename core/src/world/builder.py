from core.src.world.repositories.map_repository import RedisMapRepository
from core.src.world.utils import async_redis_pool_factory
from core.src.auth.builder import strict_redis
from core.src.world.repositories.data_repository import RedisDataRepository


world_repository = RedisDataRepository(strict_redis)
map_repository = RedisMapRepository(async_redis_pool_factory)
