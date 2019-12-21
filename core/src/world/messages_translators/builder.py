from core.src.world.messages_translators.follow_translator import TranslatorFollowItalian
from core.src.world.messages_translators.look_translator import TranslatorLookItalian
from core.src.world.messages_translators.movement_translator import TranslatorMovementsItalian
from core.src.world.messages_translators.translators_factory import MessagesTranslator

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
