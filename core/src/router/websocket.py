import json

import time
from flask_socketio import emit

from core.src.business.character import exceptions
from core.src.utils import ensure_websocket_authentication, deserialize_message
from core.src.builder import auth_service, redis_characters_index_repository, ws_channels_repository, \
    psql_character_repository
from core.src.world.builder import world_entities_repository
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.created_at import CreatedAtComponent
from core.src.world.components.name import NameComponent
from core.src.world.entity import Entity

WS_MOTD = """{}\n\n

            #########################################################################
            
            ██████╗ ██████╗  ██████╗      ██╗███████╗ ██████╗████████╗    ███╗   ███╗
            ██╔══██╗██╔══██╗██╔═══██╗     ██║██╔════╝██╔════╝╚══██╔══╝    ████╗ ████║
            ██████╔╝██████╔╝██║   ██║     ██║█████╗  ██║        ██║       ██╔████╔██║
            ██╔═══╝ ██╔══██╗██║   ██║██   ██║██╔══╝  ██║        ██║       ██║╚██╔╝██║
            ██║     ██║  ██║╚██████╔╝╚█████╔╝███████╗╚██████╗   ██║       ██║ ╚═╝ ██║
            ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚════╝ ╚══════╝ ╚═════╝   ╚═╝       ╚═╝     ╚═╝
            
            #########################################################################
                                                                                     
                                                                    Ver 0.0.1
            
                                                                ##################
\n\n\n\n"""


def build_base_websocket_route(socketio):
    @socketio.on('connect')
    @ensure_websocket_authentication
    def connect():
        emit('msg', {'data': WS_MOTD})

    @socketio.on('create')
    @ensure_websocket_authentication
    @deserialize_message(json.loads)
    def create_character(payload):
        token = auth_service.decode_session_token(payload['token'])
        assert token['context'] == 'world'
        entity = Entity().set(NameComponent(payload["name"])).set(CreatedAtComponent(int(time.time())))
        entity = world_entities_repository.save_entity(entity)
        character_id = psql_character_repository.store_new_character(NameComponent.get(entity.entity_id))
        redis_characters_index_repository.set_entity_id(character_id, entity.entity_id)
        emit('create', {'success': True, 'character_id': character_id})

    @socketio.on('auth')
    @ensure_websocket_authentication
    @deserialize_message(json.loads)
    def authenticate_character(payload):
        token = auth_service.decode_session_token(payload['token'])
        assert token['context'] == 'world'
        entity_id = redis_characters_index_repository.get_entity_id(token['data']['character_id'])
        if not entity_id:
            raise exceptions.CharacterNotAllocated('create first')
        channel = ws_channels_repository.create(entity_id)
        entity = Entity(entity_id).set(ConnectionComponent(channel.connection_id))
        world_entities_repository.update_entity(entity)
        emit('auth', {'data': {'channel_id': channel.connection_id}})
