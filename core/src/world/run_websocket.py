import asyncio

from aiohttp import web
from core.src.world.builder import websocket_channels_service, async_redis_queue
from core.src.world.services.redis_pubsub_interface import PubSubManager
from core.src.world.services.transport.redis_pubsub_subscriber_service import RedisPubSubSystemEventsSubscriberService
from core.src.world.services.transport.websocket_namespace_main import sio
from core.src.world.services.transport.websocket_system_events_observer import TransportSystemEventsObserver
from etc import settings

app = web.Application()
sio.attach(app)

system_events_observer = TransportSystemEventsObserver()
system_events_observer.add_transport_service(websocket_channels_service)
pubsub = PubSubManager(async_redis_queue)
system_events_subscribe = RedisPubSubSystemEventsSubscriberService(pubsub)
system_events_subscribe.add_observer_for_topic('system.transport', system_events_observer)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    websocket_channels_service.set_socketio_instance(sio).set_event_loop(loop)
    loop.create_task(websocket_channels_service.start())
    loop.create_task(pubsub.start())
    loop.create_task(system_events_subscribe.subscribe_transport_system_messages())
    web.run_app(app, host=settings.SOCKETIO_HOSTNAME, port=settings.SOCKETIO_PORT)
