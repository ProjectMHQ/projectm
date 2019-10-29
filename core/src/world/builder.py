from core.src.builder import strict_redis
from core.src.world.repositories.components_repository import ComponentsRepository
from core.src.world.repositories.entities_repository import EntitiesRepository


world_entities_repository = EntitiesRepository(strict_redis),
world_components_repository = ComponentsRepository(strict_redis)
