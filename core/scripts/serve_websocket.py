import asyncio
import socketio
from aiohttp import web
import json
import time
from core.scripts.monitor_websocket_channels import builder
from core.src.business.character import exceptions
from core.src.builder import auth_service, redis_characters_index_repository, ws_channels_repository, \
    psql_character_repository
from core.src.logging_factory import LOGGER
from core.src.world.builder import world_repository
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.created_at import CreatedAtComponent
from core.src.world.components.name import NameComponent
from core.src.world.entity import Entity
from core.src.utils import deserialize_message
from etc import settings

mgr = socketio.AsyncRedisManager('redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT))
sio_settings = dict(client_manager=mgr, async_mode='aiohttp')
if settings.ENABLE_CORS:
    sio_settings['cors_allowed_origins'] = '*'

loop = asyncio.get_event_loop()
sio = socketio.AsyncServer(**sio_settings)
app = web.Application()
sio.attach(app)


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


@sio.event
async def connect(sid, environ):
    LOGGER.core.debug('Sending MOTD')
    await sio.emit('msg', {'data': WS_MOTD})


@sio.on('create')
@deserialize_message(json.loads)
async def create_character(sid, payload):
    token = auth_service.decode_session_token(payload['token'])
    assert token['context'] == 'world'
    entity = Entity().set(NameComponent(payload["name"])).set(CreatedAtComponent(int(time.time())))
    entity = world_repository.save_entity(entity)
    character_id = psql_character_repository.store_new_character(NameComponent.get(entity.entity_id))
    redis_characters_index_repository.set_entity_id(character_id, entity.entity_id)
    await sio.emit('create', {'success': True, 'character_id': character_id})


@sio.on('auth')
@deserialize_message(json.loads)
async def authenticate_character(sid, payload):
    token = auth_service.decode_session_token(payload['token'])
    assert token['context'] == 'world'
    entity_id = redis_characters_index_repository.get_entity_id(token['data']['character_id'])
    if not entity_id:
        raise exceptions.CharacterNotAllocated('create first')
    channel = ws_channels_repository.create(entity_id)
    entity = Entity(entity_id).set(ConnectionComponent(channel.connection_id))
    world_repository.update_entity(entity)
    await sio.emit('auth', {'data': {'channel_id': channel.connection_id}})


if __name__ == '__main__':
    ws_channels_monitor = builder(sio)
    loop.create_task(ws_channels_monitor.start())
    web.run_app(app, host=settings.SOCKETIO_HOSTNAME, port=settings.SOCKETIO_PORT)
