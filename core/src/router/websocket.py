import json
from flask import request
from flask_socketio import emit
from core.src.authentication.scope import ensure_websocket_authentication
from core.src.builder import auth_service, redis_character_repository
from core.src.websocket.builder import ws_messages_factory
from core.src.websocket.utilities import deserialize_message
from core.src.world.builder import world_entities_repository, world_components_repository
from core.src.world.domain.components import Components
from core.src.world.types import Bit


def build_base_websocket_route(socketio):
    @socketio.on('connect')
    @ensure_websocket_authentication
    def connect():
        """
        The main WS Channel. Not "World" related.
        :return:
        """
        emit('msg', {
            'data': ws_messages_factory.get_motd(),
            'ctx': 'auth'
        })
        emit('msg', {
            'data': ws_messages_factory.get_login_message(request),
            'ctx': 'auth'
        })

    @socketio.on('auth')
    @ensure_websocket_authentication
    @deserialize_message(json.loads)
    def authentication(payload):
        emit('msg', {'data': ws_messages_factory.wait_for_auth(), 'ctx': 'auth'})
        token = auth_service.decode_session_token(payload['token'])
        assert token['context'] == 'world'
        entity_id = redis_character_repository.get_entity_id(payload['character_id'])
        if not entity_id:
            entity_id = world_entities_repository.create_entity()
            redis_character_repository.set_entity_id(payload['character_id'], entity_id)
        channel_id = websocket_channels_repository.get_channel_for_entity(entity_id)
        world_entities_repository.update_entity_properties(entity_id, connection_id=channel_id)
        world_components_repository.component_on(Components.base.CONNECTION, entity_id)
        emit('auth', {'data': {'channel_id': channel_id}})
