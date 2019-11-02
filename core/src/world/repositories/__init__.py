import typing

from core.src.world.repositories.character_repository import RedisCharacterRepositoryImpl
from core.src.world.repositories.world_repository import RedisWorldRepositoryImpl

RepositoriesFactory = typing.NamedTuple(
    'RepositoriesFactory',
    (
        ('world', RedisWorldRepositoryImpl),
        ('character', RedisCharacterRepositoryImpl)
    )
)
