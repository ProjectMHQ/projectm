import json

from flask import request
from flask_socketio import emit

from core.src.authentication.scope import ensure_websocket_authentication
from core.src.builder import ws_messages_factory


def build_websocket_route(socketio):
    @socketio.on('connect')
    @ensure_websocket_authentication
    def connect():
        emit('msg', {'data': ws_messages_factory.get_motd()})
        emit('msg', {'data': ws_messages_factory.get_login_message()})
        emit('msg', {'data': json.dumps(request.user_token, indent=4)})

    @socketio.on('msg')
    def message(message):
        emit('msg', {'data': str(message)})

    @socketio.on('authetication')
    def authentication():
        websocket_auth_response = {}
        emit('authentication', {'data': websocket_auth_response})
