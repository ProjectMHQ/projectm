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
            "u_success": "verso l'alto",
            "d_success": "verso il basso"
        }['{}_{}'.format(direction, context)]

    @staticmethod
    def _receiver_direction_to_adjective(direction: str, context: str):
        return {
            "n_join": "da nord",
            "s_join": "da sud",
            "w_join": "da ovest",
            "e_join": "da est",
            "u_join": "dall'alto",
            "d_join": "dal basso",

            "n_leave": "verso nord",
            "s_leave": "verso sud",
            "w_leave": "verso ovest",
            "e_leave": "verso est",
            "u_leave": "verso l'alto",
            "d_leave": "verso il basso"
        }['{}_{}'.format(direction, context)]

    @staticmethod
    def _receiver_speed_to_adjective(speed: int, context: str):
        return {
            "1_join": 'arriva di corsa',
            "2_join": 'arriva scattando',
            "3_join": 'arriva camminando a passo svelto',
            "4_join": 'arriva camminando',
            "5_join": 'arriva passeggiando',
            "6_join": 'arriva lentamente',

            "1_leave": 'va di corsa',
            "2_leave": 'scatta',
            "3_leave": 'cammina a passo svelto',
            "4_leave": 'cammina',
            "5_leave": 'passeggia',
            "6_leave": 'va lentamente'
        }['{}_{}'.format(speed, context)]

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

    def translate_for_receivers(self, payload: typing.Dict) -> str:
        assert payload['event'] == self.event
        if payload['entity']['name']:
            message = "{}, ".format(payload['entity']['name'].capitalize())
        else:
            message = '{} '.format(payload['entity']['excerpt'].capitalize())
        message += '{} {}.'.format(
            self._receiver_speed_to_adjective(1, payload['action']),
            self._receiver_direction_to_adjective(payload['direction'], payload['action'])
        )
        return message
