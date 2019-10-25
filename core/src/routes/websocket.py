from flask_socketio import emit

from core.src.authentication.scope import ensure_websocket_authentication
from core.src.builder import ws_messages_factory


def build_websocket_route(socketio):
    @socketio.on('connect')
    @ensure_websocket_authentication
    def connect():
        emit('message', {'data': ws_messages_factory.get_motd()})
        emit('message', {'data': ws_messages_factory.get_login_message()})

    @socketio.on('message')
    def message():
        emit('message', {'data': 'message received'})
