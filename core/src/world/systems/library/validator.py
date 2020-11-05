from pycomb import combinators


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
    name="AttributesComponentValidator",
    strict=True
)

InventoryComponentValidator = combinators.struct(
    {
        "content": combinators.list(combinators.String),
        "max_items": combinators.Int
    },
    name="InventoryComponent"
)

GenericContainerValidator = combinators.struct(
    {
        "libname": combinators.subtype(
            combinators.String,
            lambda x: string_size(x, 16)
        ),
        "components": combinators.struct(
            {
                "attributes": AttributesComponentValidator,
                "collectible": combinators.Boolean,
                "inventory": InventoryComponentValidator
            }
        ),
    },
    name="LibraryJSONFileValidator",
    strict=True
)


LibraryJSONFileValidator = combinators.union(
    GenericContainerValidator
)
