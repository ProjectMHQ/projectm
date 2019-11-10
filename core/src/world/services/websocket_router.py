import asyncio
import socketio
from aiohttp import web
import time

from core.src.world.builder import world_repository, websocket_channels_service
from core.src.auth.business.character import exceptions
from core.src.auth.builder import auth_service, redis_characters_index_repository, ws_channels_repository, \
    psql_character_repository
from core.src.auth.logging_factory import LOGGER
from core.src.world.components.character import CharacterComponent
from core.src.world.components.created_at import CreatedAtComponent
from core.src.world.components.name import NameComponent
from core.src.world.entity import Entity

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
    await sio.emit('msg', {'data': WS_MOTD}, to=sid)
    sio.event()


@sio.on('create')
async def create_character(sid, payload):
    token = auth_service.decode_session_token(payload['token'])
    assert token['context'] == 'world:create'
    entity = Entity() \
        .set(CharacterComponent(True))\
        .set(CreatedAtComponent(int(time.time()))) \
        .set(NameComponent(payload["name"]))

    entity = world_repository.save_entity(entity)
    """
    patchwork starts here
    """
    from core.src.auth.database import init_db, db
    init_db(db)
    character_id = psql_character_repository.store_new_character(
        token['data']['user_id'], payload["name"]
    ).character_id
    try:
        db.close()
    except:
        # FIXME - This shouldn't be here, but we miss the "store_new_character" HTTP endpoint yet.
        pass
    """
    patchwork ends here
    """
    redis_characters_index_repository.set_entity_id(character_id, entity.entity_id)
    await sio.emit('create', {'success': True, 'character_id': character_id}, to=sid)


@sio.on('auth')
async def authenticate_character(sid, payload):
    token = auth_service.decode_session_token(payload['token'])
    assert token['context'] == 'world:auth'
    entity_id = redis_characters_index_repository.get_entity_id(token['data']['character_id'])
    if not entity_id:
        raise exceptions.CharacterNotAllocated('create first')
    channel = ws_channels_repository.create(entity_id)
    await websocket_channels_service.enable_channel(channel)
    await sio.emit('auth', {'data': {
        'channel_id': channel.connection_id,
        'character_id': token['data']['character_id']
    }}, to=sid)
