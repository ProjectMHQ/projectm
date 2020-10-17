import typing


class TranslatorFollowItalian:
    def __init__(self):
        self.event = 'follow'
        self.language = 'it'

    def translate_for_emitter(self, payload: typing.Dict) -> str:
        assert payload['event'] == self.event
        if payload['action'] == 'follow':
            if payload['status'] == 'success':
                return 'Segui {}'.format(payload['alias'])
            elif payload['status'] == 'failure':
                if payload['reason'] == 'repeat':
                    return "Stai gia' seguendo qualcuno"
                elif payload['reason'] == 'loop':
                    return "Non e' possibile seguirsi a vicenda"
                elif payload['reason'] == 'not_found':
                    return "Non lo vedi qui"
                else:
                    raise ValueError(payload)

        elif payload['action'] == 'unfollow':
            return 'Fatto'
        elif payload['action'] == 'move':
            return 'Segui {} verso {}'.format(payload['alias'], self._get_direction(payload['direction']))
        else:
            raise ValueError(payload)

    def translate_for_receivers(self, payload: typing.Dict) -> str:
        assert payload['event'] == self.event
        if payload['origin']['known']:
            alias = payload['origin']['name']
        else:
            alias = payload['origin']['excerpt']
        if payload['action'] == 'follow':
            return '{} comincia a seguirti'.format(alias)
        elif payload['action'] == 'unfollow':
            return '{} smette di seguirti'.format(alias)
        else:
            raise ValueError

    @staticmethod
    def _get_direction(d: str):
        return {
            "n": "nord",
            "s": "sud",
            "w": "ovest",
            "e": "est",
            "u": "l'alto",
            "d": "il basso"
        }[d]
