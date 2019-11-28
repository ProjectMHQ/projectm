class WorldException(Exception):
    pass


class EntityAlreadySavedException(WorldException):
    pass


class NotImplementedException(WorldException):
    pass


class RoomError(WorldException):
    pass
