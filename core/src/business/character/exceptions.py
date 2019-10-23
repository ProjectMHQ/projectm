class CharacterException(Exception):
    pass


class CharacterAlreadyAllocated(CharacterException):
    pass


class CharacterNotAllocated(CharacterException):
    pass

