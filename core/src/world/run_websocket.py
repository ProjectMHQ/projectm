import asyncio

from aiohttp import web
from core.src.world.builder import websocket_channels_service
from core.src.world.services.websocket.websocket_namespace_main import sio
from etc import settings

app = web.Application()
sio.attach(app)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    websocket_channels_service.set_socketio_instance(sio).set_event_loop(loop)
    loop.create_task(websocket_channels_service.start())
    web.run_app(app, host=settings.SOCKETIO_HOSTNAME, port=settings.SOCKETIO_PORT)
