import asyncio
import socketio
from aiohttp import web
import time
from redis import StrictRedis

from core.src.world.services.redis_queue import RedisMultipleQueuesPublisher
from core.src.world.utils import async_redis_pool_factory
from core.src.auth.business.character import exceptions
from core.src.auth.builder import auth_service, redis_characters_index_repository, ws_channels_repository, \
    psql_character_repository
from core.src.auth.logging_factory import LOGGER
from core.src.auth.repositories import WebsocketChannelsRepository
from core.src.world.builder import world_repository
from core.src.world.components.character import CharacterComponent
from core.src.world.components.created_at import CreatedAtComponent
from core.src.world.components.name import NameComponent
from core.src.world.entity import Entity
from core.src.world.services.websocket_channels_service import WebsocketChannelsService
from core.src.world.systems.commands.system import CommandsSystem

from etc import settings

mgr = socketio.AsyncRedisManager('redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT))
sio_settings = dict(client_manager=mgr, async_mode='aiohttp')
if settings.ENABLE_CORS:
    sio_settings['cors_allowed_origins'] = '*'

loop = asyncio.get_event_loop()
sio = socketio.AsyncServer(**sio_settings)
app = web.Application()

sio.attach(app)

"""
LRT START

Here, at the moment, I assume there is only 1 process for the websocket task, with no concurrency.
This means the monitor and all the others LRT should be ported into another process, in case 
we need to scale the WS endpoints.

"""
redis_data = StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
channels_repository = WebsocketChannelsRepository(redis_data)
redis_queues_service = RedisMultipleQueuesPublisher(
    async_redis_pool_factory, num_queues=settings.WORKERS
)
websocket_channels_service = WebsocketChannelsService(sio, channels_repository, loop)
commands_system = CommandsSystem(redis_queues_service, websocket_channels_service)
websocket_channels_service.add_on_cmd_observer(commands_system)
loop.create_task(websocket_channels_service.start())

"""
LRT END
"""

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


@sio.on('create')
async def create_character(sid, payload):
    token = auth_service.decode_session_token(payload['token'])
    assert token['context'] == 'world:create'
    entity = Entity() \
        .set(CharacterComponent(True))\
        .set(CreatedAtComponent(int(time.time()))) \
        .set(NameComponent(payload["name"]))

    entity = world_repository.save_entity(entity)
    character_id = psql_character_repository.store_new_character(
        token['data']['user_id'], payload["name"]
    ).character_id
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


if __name__ == '__main__':
    web.run_app(app, host=settings.SOCKETIO_HOSTNAME, port=settings.SOCKETIO_PORT)
