class WorldException(Exception):
    pass


class EntityAlreadySavedException(WorldException):
    pass


class NotImplementedException(WorldException):
    pass


class RoomError(WorldException):
    pass


class FollowSystemLoopError(WorldException):
    pass


class FollowSystemRepeatError(WorldException):
    pass
