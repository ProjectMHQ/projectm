from pycomb import combinators
from core.src.world.components.weapon import WeaponType


def string_size(value, size):
    if len(value) > size:
        raise ValueError('string too big')
    return value


def is_enum(value, enum):
    return enum(value)


AttributesComponentValidator = combinators.struct(
    {
        "keyword": combinators.subtype(
            combinators.String,
            lambda x: string_size(x, 16)
        ),
        "name": combinators.subtype(
            combinators.String,
            lambda x: string_size(x, 32)
        ),
        "description": combinators.subtype(
            combinators.String,
            lambda x: string_size(x, 512)
        ),
    },
    name="AttributesComponentValidator"
)

WeaponComponentValidator = combinators.subtype(
    combinators.String,
    lambda x: is_enum(x, WeaponType),
    name="WeaponComponentValidator"
)

LibraryJSONFileValidator = combinators.struct(
    {
        "alias": combinators.subtype(
            combinators.String,
            lambda x: string_size(x, 16)
        ),
        "components": combinators.struct(
            {
                "attributes": AttributesComponentValidator,
                "weapon": WeaponComponentValidator
            }
        )
    },
    name="LibraryJSONFileValidator"
)
