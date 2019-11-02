import asyncio
from flask_socketio import SocketIO
from redis import StrictRedis
import time

from etc import settings
from core.src.logging_factory import LOGGER
from core.src.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository

"""
this agent is intended to monitor the websockets channels statuses with PING\PONG messages.

check PING_INTERVAL & PING_TIMEOUT options
"""


class WebsocketChannelsMonitor:
    def __init__(
            self,
            socketio: SocketIO,
            channels_repository: WebsocketChannelsRepository,
            loop=asyncio.get_event_loop()
    ):
        self.loop = loop
        self.connections_statuses = {}
        self.socketio = socketio
        self.channels_repository = channels_repository
        self.ping_interval = 30
        self.ping_timeout = 90

    def _on_presence_event(self, connection_id: str, message: str):
        LOGGER.websocket_monitor.debug(
            'Received message [ %s ] from connection_id [ %s ]', message, connection_id
        )
        if message == 'PONG':
            self.connections_statuses[connection_id]['last_pong'] = int(time.time())
        if message == 'PING':
            if connection_id in self.connections_statuses:
                socketio.emit('presence', 'PONG', namespace=connection_id)

    def subscribe_pong_from_channels(self, connection_id: str):
        LOGGER.websocket_monitor.info('Subscribe presence for channel %s', connection_id)
        self.socketio.on_event(
            'presence', lambda m: self._on_presence_event(connection_id, m), namespace=connection_id
        )

    def ping_channel(self, connection_id: str):
        LOGGER.websocket_monitor.debug('Sending PING message to connection_id [ %s ]', connection_id)
        self.connections_statuses[connection_id]['last_ping'] = int(time.time())
        self.socketio.emit('presence', 'PING', namespace=connection_id)

    async def start(self):
        while 1:
            await self.monitor_connection_statuses()
            await asyncio.sleep(0.1)

    async def monitor_connection_statuses(self):
        channels = self.channels_repository.get_active_channels()
        for channel in channels:
            self.loop.create_task(self._check_connection_status(channel))

    async def _check_connection_status(self, channel):
        now = int(time.time())

        if not self.connections_statuses.get(channel.connection_id):
            LOGGER.websocket_monitor.debug('Channel %s status never saved. Saving', channel)
            self.connections_statuses[channel.connection_id] = {"seen_at": channel.created_at}
            self.subscribe_pong_from_channels(channel.connection_id)

        if not self.connections_statuses[channel.connection_id].get('last_ping') or now -\
                self.connections_statuses[channel.connection_id]['last_ping'] > self.ping_interval:
            self.ping_channel(channel.connection_id)

        if (self.connections_statuses[channel.connection_id].get('last_pong') and
            now - self.connections_statuses[channel.connection_id]['last_pong'] > self.ping_timeout) or \
                (not self.connections_statuses[channel.connection_id].get('last_pong') and
                 now - self.connections_statuses[channel.connection_id]['seen_at'] > self.ping_timeout):
            LOGGER.websocket_monitor.info('Ping timeout for channel %s', channel)
            self.channels_repository.delete(channel.connection_id)


if __name__ == '__main__':
    redis = StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    loop = asyncio.get_event_loop()
    socketio = SocketIO(message_queue='redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT))
    channels_factory = WebsocketChannelsRepository(redis)
    monitor = WebsocketChannelsMonitor(socketio, channels_factory, loop=loop)
    loop.create_task(monitor.start())
    loop.run_forever()
