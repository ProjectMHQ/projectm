import typing

from core.src.world.actions.look.look_translator import TranslatorLookItalian
from core.src.world.actions.movement.follow_translator import TranslatorFollowItalian
from core.src.world.actions.movement.movement_translator import TranslatorMovementsItalian


class MessagesTranslator:
    def __init__(self):
        self._strategies_by_topic = {}

    def add_translation_strategy(self, topic, strategy):
        if not self._strategies_by_topic.get(topic):
            self._strategies_by_topic[topic] = {}
        self._strategies_by_topic[topic][strategy.event] = strategy

    def payload_msg_to_string(self, payload, topic) -> typing.Dict:
        if topic not in self._strategies_by_topic:
            return payload
        try:
            translator_strategy = self._strategies_by_topic[topic][payload['event']]
            return translator_strategy.translate_for_emitter(payload)
        except KeyError:
            return payload

    def event_msg_to_string(self, event, topic) -> typing.Dict:
        if topic not in self._strategies_by_topic:
            return event
        try:
            translator_strategy = self._strategies_by_topic[topic][event['event']]
            return translator_strategy.translate_for_receivers(event)
        except KeyError:
            raise


TRANSLATORS = {
    'it': {
        'msg': [
            TranslatorMovementsItalian,
            TranslatorLookItalian,
            TranslatorFollowItalian
        ],
    }
}


def get_messages_translator(language) -> MessagesTranslator:
    language_translators = TRANSLATORS[language]
    translator = MessagesTranslator()
    for topic, translator_strategies in language_translators.items():
        for strategy in translator_strategies:
            translator.add_translation_strategy(topic, strategy())
    return translator
