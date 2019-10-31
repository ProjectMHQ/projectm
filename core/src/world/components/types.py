import enum


class ComponentType(enum.Enum):
    pass


class BaseComponentType(ComponentType):
    CREATED_AT = 'created_at'
    CONNECTION = 'connection'
    POS = 'pos'
    NAME = 'name'
