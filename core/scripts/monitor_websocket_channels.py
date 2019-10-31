import asyncio
from redis import StrictRedis
from core.src.logging_factory import LOGGING_FACTORY
from core.src.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from etc import settings
from flask_socketio import SocketIO


class WebsocketChannelsMonitor:
    def __init__(
            self,
            socketio: SocketIO,
            channels_repository: WebsocketChannelsRepository,
            loop=asyncio.get_event_loop()
    ):
        self.loop = loop
        self.last_ping = {}
        self.socketio = socketio
        self.channels_repository = channels_repository

    async def start(self):
        while 1:
            channels = self.channels_repository.get_active_channels()
            for channel in channels:
                print('Sending ping on channel %s (entity %s)' % (channel.channel_id, channel.entity_id))
                self.socketio.emit(
                    'msg', 'PING {}'.format(channel.connection_id), namespace='/' + channel.channel_id
                )
            LOGGING_FACTORY.websocket_monitor.debug('Sleeping')
            await asyncio.sleep(3)


if __name__ == '__main__':
    redis = StrictRedis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB
    )
    loop = asyncio.get_event_loop()
    socketio = SocketIO(message_queue='redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT))
    channels_factory = WebsocketChannelsRepository(redis)
    monitor = WebsocketChannelsMonitor(socketio, channels_factory, loop=loop)
    loop.run_until_complete(monitor.start())
