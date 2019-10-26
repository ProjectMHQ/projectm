import typing

RepositoriesFactory = typing.NamedTuple(
    'RepositoriesFactory',
    (
        ('world', callable),
        ('character', callable)
    )
)
