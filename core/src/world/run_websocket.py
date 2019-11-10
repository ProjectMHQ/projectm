from aiohttp import web

from core.src.world.builder import websocket_channels_service
from core.src.world.services.websocket_router import sio, loop, app
from etc import settings

if __name__ == '__main__':
    websocket_channels_service \
        .set_socketio_instance(sio) \
        .set_event_loop(loop)
    loop.create_task(websocket_channels_service.start())
    web.run_app(app, host=settings.SOCKETIO_HOSTNAME, port=settings.SOCKETIO_PORT)
