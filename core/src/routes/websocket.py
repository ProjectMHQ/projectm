from flask_socketio import emit
from core.src.builder import ws_messages_factory


def build_websocket_route(socketio):
    @socketio.on('connect')
    def connect():
        emit('message', {'data': ws_messages_factory.get_motd()})
        emit('message', {'data': ws_messages_factory.get_login_message()})
        #websocket_event_listener.on_connect()

    @socketio.on('msg')
    def message():
        emit('message', {'data': 'message received'})
        #websocket_event_listener.on_message()

    @socketio.on('authetication')
    def authentication():
        websocket_auth_response = {}
        emit('authentication', {'data': websocket_auth_response})
        #websocket_event_listener.on_authentication()
