import time

from core.src.auth.business.character import exceptions
from core.src.auth.builder import auth_service, redis_characters_index_repository, ws_channels_repository, \
    psql_character_repository
from core.src.auth.logging_factory import LOGGER
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.character import CharacterComponent
from core.src.world.components.created_at import CreatedAtComponent
from core.src.world.entity import Entity


WS_MOTD = """Project M\n"""


def build_public_namespace(sio, world_repository, websocket_channels_service):
    @sio.event
    async def connect(sid, environ):
        LOGGER.core.debug('Sending MOTD')
        await sio.emit('system', {'data': WS_MOTD}, to=sid)

    @sio.on('create')
    async def create_character(sid, payload):
        token = auth_service.decode_session_token(payload['token'])
        assert token['context'] == 'world:create'
        entity = Entity() \
            .set(CharacterComponent(True))\
            .set(CreatedAtComponent(int(time.time()))) \
            .set(AttributesComponent({"name": payload["name"]}))

        entity = await world_repository.save_entity(entity)
        """
        URGENT - TODO - FIX - Completely move characters allocation outside of SQL.
        Create a "UserID Component" to pair the character in the ECS with the ecosystem uuid,
        as we do for the connection.
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
        Fix ends here, probably
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
            'channel_id': channel.id,
            'character_id': token['data']['character_id']
        }}, to=sid)
