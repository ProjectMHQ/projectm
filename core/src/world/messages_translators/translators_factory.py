import typing


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
