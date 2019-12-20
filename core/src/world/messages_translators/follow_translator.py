import json
import typing


class TranslatorFollowItalian:
    def __init__(self):
        self.event = 'follow'
        self.language = 'it'

    def translate_for_emitter(self, payload: typing.Dict) -> str:
        assert payload['event'] == self.event
        return json.dumps(payload)

    def translate_for_receivers(self, payload: typing.Dict) -> str:
        assert payload['event'] == self.event
        return json.dumps(payload)
