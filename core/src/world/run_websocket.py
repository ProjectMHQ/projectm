import socketio
from aiohttp import web
from core.src.world.builder import websocket_channels_service, async_redis_queue, world_repository
from core.src.world.services.redis_pubsub_interface import PubSubManager
from core.src.world.transport.redis_pubsub_subscriber_service import RedisPubSubSystemEventsSubscriberService
from core.src.world.transport.websocket_namespace_main import build_public_namespace
from core.src.world.transport.websocket_system_events_observer import TransportSystemEventsObserver
from etc import settings


mgr = socketio.AsyncRedisManager('redis://{}:{}/{}'.format(
    settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_SIO_DB)
)
sio_settings = dict(client_manager=mgr, async_mode='aiohttp')
if settings.ENABLE_CORS:
    sio_settings['cors_allowed_origins'] = '*'

sio = socketio.AsyncServer(**sio_settings)

app = web.Application()
sio.attach(app)

system_events_observer = TransportSystemEventsObserver()
system_events_observer.add_transport_service(websocket_channels_service)
pubsub = PubSubManager(async_redis_queue)
system_events_subscribe = RedisPubSubSystemEventsSubscriberService(pubsub)
system_events_subscribe.add_observer_for_topic('system.transport', system_events_observer)

if __name__ == '__main__':
    import asyncio

    loop = asyncio.get_event_loop()
    websocket_channels_service.set_socketio_instance(sio).set_event_loop(loop)
    loop.create_task(websocket_channels_service.start())
    loop.create_task(pubsub.start())
    loop.create_task(system_events_subscribe.subscribe_transport_system_messages())
    build_public_namespace(sio, world_repository, websocket_channels_service)
    web.run_app(app, host=settings.SOCKETIO_HOSTNAME, port=settings.SOCKETIO_PORT)
