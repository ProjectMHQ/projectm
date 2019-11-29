import typing


class TranslatorMovementsItalian:
    def __init__(self):
        self.event = 'move'
        self.language = 'it'

    @staticmethod
    def _emitter_speed_to_adjective(speed: int, context: str):
        return {
            "1_begin": 'Inizi a muoverti di corsa',
            "2_begin": 'Inizi a muoverti, scattando',
            "3_begin": 'Inizi a muoverti, camminando a passo svelto',
            "4_begin": 'Inizi a muoverti, camminando',
            "5_begin": 'Inizi a muoverti, passeggiando',
            "6_begin": 'Inizi a muoverti lentamente',

            "1_success": 'Vai di corsa',
            "2_success": 'Scatti',
            "3_success": 'Cammini a passo svelto',
            "4_success": 'Cammini',
            "5_success": 'Passeggi',
            "6_success": 'Vai lentamente'
        }['{}_{}'.format(speed, context)]

    @staticmethod
    def _emitter_direction_to_adjective(direction: str, context: str):
        return {
            "n_begin": "verso nord",
            "s_begin": "verso sud",
            "w_begin": "verso ovest",
            "e_begin": "verso est",
            "u_begin": "verso l'alto",
            "d_begin": "verso il basso",

            "n_success": "a nord",
            "s_success": "a sud",
            "w_success": "a ovest",
            "e_success": "a est",
            "u_success": "verso alto",
            "d_success": "verso il basso"
        }['{}_{}'.format(direction, context)]

    def translate_for_emitter(self, payload: typing.Dict) -> str:
        assert payload['event'] == self.event
        if payload['status'] == 'begin':
            return "{} {}".format(
                self._emitter_speed_to_adjective(payload['speed'], 'begin'),
                self._emitter_direction_to_adjective(payload['direction'], 'begin')
            )
        if payload['status'] == 'success':
            return '{} {}'.format(
                self._emitter_speed_to_adjective(payload['speed'], 'success'),
                self._emitter_direction_to_adjective(payload['direction'], 'success')
            )
        if payload['status'] == 'error':
            return 'Non puoi andare in quella direzione'

    def translate_for_receivers(self, event: typing.Dict):
        pass
