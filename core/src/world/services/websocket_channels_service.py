import asyncio
from redis import StrictRedis
import time

from socketio import AsyncRedisManager

from etc import settings
from core.src.auth.logging_factory import LOGGER
from core.src.auth.repositories import WebsocketChannelsRepository

"""
this agent is intended to monitor the websockets channels statuses with PING\PONG messages.

check PING_INTERVAL & PING_TIMEOUT options

It also emits events to \ from established channels
"""


class WebsocketChannelsService:
    def __init__(
            self,
            socketio,
            channels_repository: WebsocketChannelsRepository,
            loop,
            ping_interval=30,
            ping_timeout=90
    ):
        self.loop = loop
        self.connections_statuses = {}
        self.socketio = socketio
        self.channels_repository = channels_repository
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self._on_delete_channel = []
        self._on_ping = []
        self._on_cmd_observers = []
        self._on_new_channel_observers = []
        self.channels_cache = {}

    def add_on_channel_delete_event(self, observer):
        self._on_delete_channel.append(observer)

    def add_on_ping_event(self, observer):
        self._on_ping.append(observer)

    def add_on_cmd_observer(self, observer):
        self._on_cmd_observers.append(observer)

    def add_on_new_channel_observer(self, observer):
        self._on_new_channel_observers.append(observer)

    async def _on_presence_event(self, connection_id: str, message: str):
        LOGGER.websocket_monitor.debug(
            'Received message [ %s ] from connection_id [ %s ]', message, connection_id
        )
        if message == 'PONG':
            self.connections_statuses[connection_id]['last_pong'] = int(time.time())
        if message == 'PING':
            if connection_id in self.connections_statuses:
                await self.socketio.emit('presence', 'PONG', namespace='/{}'.format(connection_id))

    async def subscribe_pong_from_channels(self, connection_id: str):
        LOGGER.websocket_monitor.info('Subscribe presence for channel %s', connection_id)

        async def cb(_, data):
            await self._on_presence_event(connection_id, data)

        self.socketio.on('presence', cb, namespace='/{}'.format(connection_id))

    async def subscribe_commands_from_channels(self, connection_id: str):
        LOGGER.websocket_monitor.info('Subscribe presence for channel %s', connection_id)

        async def cb(_, data):
            for observer in self._on_cmd_observers:
                self.loop.create_task(
                    observer.on_message(connection_id, self.channels_cache[connection_id], data)
                )

        self.socketio.on('cmd', cb, namespace='/{}'.format(connection_id))

    async def ping_channel(self, connection_id: str):
        LOGGER.websocket_monitor.debug('Sending PING message to connection_id [ %s ]', connection_id)
        self.connections_statuses[connection_id]['last_ping'] = int(time.time())
        await self.socketio.emit('presence', 'PING', namespace='/{}'.format(connection_id))

    async def start(self):
        while 1:
            await self.monitor_connection_statuses()
            await asyncio.sleep(1)

    async def monitor_connection_statuses(self):
        channels = self.channels_repository.get_active_channels()
        for channel in channels:
            self.loop.create_task(self._check_connection_status(channel))

    async def on_message(self, topic, message, namespace):
        self.loop.create_task(
            self.socketio.emit(topic, message, namespace='/{}'.format(namespace))
        )

    async def enable_channel(self, channel):
        await self._check_connection_status(channel)

    async def _check_connection_status(self, channel):
        now = int(time.time())
        self.channels_cache[channel.connection_id] = channel.entity_id
        if not self.connections_statuses.get(channel.connection_id):
            LOGGER.websocket_monitor.debug('Channel %s status never saved. Saving', channel)
            self.connections_statuses[channel.connection_id] = {"seen_at": channel.created_at}
            await asyncio.gather(
                self.subscribe_pong_from_channels(channel.connection_id),
                self.subscribe_commands_from_channels(channel.channel_id)
            )
            self.loop.create_task(
                asyncio.gather(
                    *(observer.on_event(channel) for observer in self._on_new_channel_observers)
                )
            )
        if not self.connections_statuses[channel.connection_id].get('last_ping') or now -\
                self.connections_statuses[channel.connection_id]['last_ping'] > self.ping_interval:
            for observer in self._on_ping:
                observer(channel.connection_id)
            await self.ping_channel(channel.connection_id)

        if (self.connections_statuses[channel.connection_id].get('last_pong') and
            now - self.connections_statuses[channel.connection_id]['last_pong'] > self.ping_timeout) or \
                (not self.connections_statuses[channel.connection_id].get('last_pong') and
                 now - self.connections_statuses[channel.connection_id]['seen_at'] > self.ping_timeout):
            LOGGER.websocket_monitor.info('Ping timeout for channel %s', channel)
            for observer in self._on_delete_channel:
                observer(channel.connection_id)
            self.channels_repository.delete(channel.connection_id)
            self.channels_cache.pop(channel.connection_id, None)


def builder(
        sio=None,
        loop=asyncio.get_event_loop(),
        redis_data=None,
        ping_interval=30,
        ping_timeout=60
):
    redis_data = redis_data or StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    socketio = sio or AsyncRedisManager('redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT))
    channels_factory = WebsocketChannelsRepository(redis_data)
    monitor = WebsocketChannelsService(
        socketio, channels_factory, loop, ping_interval=ping_interval, ping_timeout=ping_timeout
    )
    return monitor
