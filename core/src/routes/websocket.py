import json

from flask import request
from flask_socketio import emit

from core.src.authentication.scope import ensure_websocket_authentication
from core.src.builder import auth_service
from core.src.websocket.builder import ws_commands_processor, ws_messages_factory
from core.src.websocket.utilities import ws_commands_extractor


def build_websocket_route(socketio):
    @socketio.on('connect')
    @ensure_websocket_authentication
    def connect():
        emit('msg', {
            'data': ws_messages_factory.get_motd(),
            'ctx': 'auth'
        })
        emit('msg', {
            'data': ws_messages_factory.get_login_message(request),
            'ctx': 'auth'
        })

    @socketio.on('msg')
    @ensure_websocket_authentication
    def message(msg):
        command, arguments = ws_commands_extractor(msg)
        if not command:
            return
        ws_commands_processor.on_command(
            command,
            arguments,
            lambda response: response and emit('msg', {
                'data': response,
                'ctx': 'cmd'
            })
        )

    @socketio.on('auth')
    @ensure_websocket_authentication
    def authentication(message):
        token = auth_service.decode_session_token(message)
        assert token['context'] == 'character'
        raise NotImplementedError ## Fixme Todo