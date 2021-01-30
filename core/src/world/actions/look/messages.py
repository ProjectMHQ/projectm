from core.src.world.utils.world_types import DirectionEnum


class LookMessages:
    def __init__(self):
        self.event = "look"
        self.language = "it"
        self._directions = {
            DirectionEnum.NORTH: "a nord",
            DirectionEnum.SOUTH: "a sud",
            DirectionEnum.EAST: "ad est",
            DirectionEnum.WEST: "a ovest",
            DirectionEnum.UP: "verso l'alto",
            DirectionEnum.DOWN: "verso il basso",
        }

    def look_at_direction(self, direction: DirectionEnum) -> str:
        return "Guardi {}".format(self._directions[direction])

    def missing_target(self):
        return "Non lo vedi qui"

    def wrong_direction(self):
        return "Non è una direzione!"

    def self_look(self):
        return "Ti guardi"

    def look_at_entity(self, entity_alias):
        return "Guardi {}".format(entity_alias)

    def entity_looks_at_you(self, lurker_entity_alias):
        return "{} ti guarda".format(lurker_entity_alias)

    def entity_looks_at_entity_template(self):
        return "{origin} guarda {target}"
