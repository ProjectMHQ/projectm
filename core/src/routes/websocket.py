from flask_socketio import emit
from core.src.builder import ws_messages_factory


def build_websocket_route(socketio):
    @socketio.on('connect')
    def connect():
        emit('message', {'data': ws_messages_factory.get_motd()})
        emit('message', {'data': ws_messages_factory.get_login_message()})

    @socketio.on('auth')
    def echo(message):
        print('Received msg: %s' % message)
        Character.authenticate(message['character_id'], message['character_token'])
        return emit()
