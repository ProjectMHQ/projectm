import json
from flask import request
from flask_socketio import emit
from core.src.authentication.scope import ensure_websocket_authentication
from core.src.builder import auth_service
from core.src.websocket.builder import _ws_world_commands_interface, ws_messages_factory, ws_commands_extractor_factory
from core.src.world.builder import repositories


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
        json_message = json.loads(msg)
        _interface = ws_commands_extractor_factory.get_interface(json_message['ctx'])
        if not json_message['data']:
            return
        _interface.on_command(
            json_message['data'],
            lambda response: response and emit('msg', {
                'data': response,
                'ctx': 'cmd'
            })
        )

    @socketio.on('auth')
    @ensure_websocket_authentication
    def authentication(message):
        payload = json.loads(message)
        emit('msg', {'data': ws_messages_factory.wait_for_auth(), 'ctx': 'auth'})
        token = auth_service.decode_session_token(payload['token'])
        assert token['context'] == 'character'
        existing_channel = repositories.world.get_character_channel(token['data']['character_id'])
        channel_id = existing_channel or repositories.world.login(token['data']['character_id'])
        emit('auth', {'data': {'channel_id': channel_id}})
