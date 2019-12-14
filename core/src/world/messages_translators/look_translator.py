import json
import typing

from core.src.world.actions.utils.utils import DirectionEnum


class TranslatorLookItalian:
    def __init__(self):
        self.event = "look"
        self.language = "it"
    
    @staticmethod
    def _get_direction_by_enum(value: DirectionEnum):
        return {
            DirectionEnum.NORTH: "a nord",
            DirectionEnum.SOUTH: "a sud",
            DirectionEnum.EAST: "ad est",
            DirectionEnum.WEST: "a ovest",
            DirectionEnum.UP: "verso l'alto",
            DirectionEnum.DOWN: "verso il basso",
        }[value]

    def _handle_direction_for_emitter(self, payload: typing.Dict) -> str:
        return "Guardi {}".format(self._get_direction_by_enum(payload["value"]))
    
    @staticmethod
    def _handle_entity_for_emitter(payload: typing.Dict) -> str:
        if payload.get("is_self"):
            return "Ti guardi"
        return "Guardi {}".format(payload["alias"])
    
    def translate_for_emitter(self, payload: typing.Dict) -> str:
        assert payload["event"] == self.event
        if payload["status"] == "failure":
            if payload["target"] == "direction":
                assert payload["reason"] == "value_error"
                return "'{}' non è una direzione!".format(payload["value"])
            elif payload["target"] == "entity":
                return "Non lo vedi qui"
        if payload["target"] == "direction":
            return self._handle_direction_for_emitter(payload)
        elif payload["target"] == "entity":
            return self._handle_entity_for_emitter(payload)

    def translate_for_receivers(self, payload: typing.Dict) -> str:
        assert payload["event"] == self.event
        origin_alias = payload['origin']['name'] if payload['origin']['known'] else payload['origin']['excerpt']
        if payload['target'] == 'self':
            return '{} ti guarda'.format(origin_alias)
        else:
            target_alias = payload['target']['name'] if payload['target']['known'] else payload['target']['excerpt']
            return '{} guarda {}'.format(origin_alias, target_alias)
