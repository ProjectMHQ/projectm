import enum
import typing


class WebsocketContext(enum.Enum):
    WORLD = 'world'


WebsocketChannel = typing.NamedTuple(
    'WebsocketChannel',
    (
        ('entity_id', str),
        ('connection_id', str),
        ('created_at', int)
    )
)
