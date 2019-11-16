import asyncio
import time
from core.src.auth.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.world.components.connection import ConnectionComponent
from core.src.world.entity import Entity
from core.src.auth.logging_factory import LOGGER

"""
this agent is intended to monitor the websockets channels statuses with PING / PONG messages.

check PING_INTERVAL & PING_TIMEOUT options

It also emits events to / from established channels
"""


class WebsocketChannelsService:
    def __init__(
            self,
            socketio=None,
            channels_repository: WebsocketChannelsRepository=None,
            loop=None,
            data_repository=None,
            redis_queue=None,
            ping_interval=30,
            ping_timeout=90
    ):
        self.loop = loop
        self.connections_statuses = {}
        self.socketio = socketio
        self.channels_repository = channels_repository
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.data_repository = data_repository
        self._on_delete_channel = []
        self._on_ping = []
        self._on_cmd_observers = []
        self._on_new_channel_observers = []
        self.channels_cache = {}
        self._pending_channels = asyncio.Queue()
        self.redis_queues_manager = redis_queue

    def set_socketio_instance(self, sio):
        self.socketio = sio
        return self

    def set_event_loop(self, loop):
        self.loop = loop
        return self

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

    def remove_handlers(self, channel):
        self.socketio.emit('disconnect', '', '/{}'.format(channel.connection_id))
        self.socketio.handlers.pop('/{}'.format(channel.connection_id), None)

    async def subscribe_pong_from_channels(self, connection_id: str):
        LOGGER.websocket_monitor.info('Subscribe presence for channel %s', connection_id)

        async def cb(_, data):
            await self._on_presence_event(connection_id, data)

        self.socketio.on('presence', cb, namespace='/{}'.format(connection_id))

    async def subscribe_commands_from_channels(self, channel):
        LOGGER.websocket_monitor.info('Subscribe commands for channel %s', channel.connection_id)

        async def cb(_, data):
            await self.redis_queues_manager.put(
                {
                    'n': channel.connection_id,
                    'e_id': channel.entity_id,
                    'd': data,
                    't': int(time.time()),
                    'c': 'cmd'
                }
            )
            for observer in self._on_cmd_observers:
                self.loop.create_task(
                    observer.on_message(
                        channel.connection_id,
                        self.channels_cache[channel.connection_id],
                        data
                    )
                )
        self.socketio.on('cmd', cb, namespace='/{}'.format(channel.connection_id))

    async def bind_channel(self, channel):
        async def _on_connect(*a, **kw):
            LOGGER.websocket_monitor.info('Channel %s connected', str(channel))
            self.connections_statuses[channel.connection_id]['open'] = True
            self.data_repository.update_entities(
                Entity(channel.entity_id).set(ConnectionComponent(channel.connection_id))
            )
            self.loop.create_task(self.subscribe_commands_from_channels(channel))
            await self.redis_queues_manager.put(
                {
                    'n': channel.connection_id,
                    'e_id': channel.entity_id,
                    't': int(time.time()),
                    'c': 'connected'
                }
            )
        self.socketio.on(
            'connect', _on_connect, namespace='/{}'.format(channel.connection_id)
        )

    async def ping_channel(self, connection_id: str):
        LOGGER.websocket_monitor.debug('Sending PING message to connection_id [ %s ]', connection_id)
        self.connections_statuses[connection_id]['last_ping'] = int(time.time())
        for event_handler in self._on_ping:
            event_handler(connection_id)
        await self.socketio.emit('presence', 'PING', namespace='/{}'.format(connection_id))

    async def start(self):
        self.loop.create_task(self.start_monitoring())
        while 1:
            channel = await self._pending_channels.get()
            self.loop.create_task(self._check_connection_status(channel))

    async def start_monitoring(self):
        while 1:
            await self.monitor_connection_statuses()
            await asyncio.sleep(1)

    async def monitor_connection_statuses(self):
        channels = self.channels_repository.get_active_channels()
        for channel in channels:
            self.loop.create_task(self._check_connection_status(channel))

    async def enable_channel(self, channel):
        self._pending_channels.put_nowait(channel)

    async def _check_connection_status(self, channel):
        now = int(time.time())
        self.channels_cache[channel.connection_id] = channel.entity_id
        if not self.connections_statuses.get(channel.connection_id):
            LOGGER.websocket_monitor.debug('Channel %s status never saved. Saving', channel)
            self.connections_statuses[channel.connection_id] = {"seen_at": int(time.time())}
            await asyncio.gather(
                self.subscribe_pong_from_channels(channel.connection_id),
                self.bind_channel(channel)
            )
            self._on_new_channel_observers and self.loop.create_task(
                asyncio.gather(
                    *(observer.on_event(channel) for observer in self._on_new_channel_observers)
                )
            )
        if self.connections_statuses[channel.connection_id].get('open'):
            if not self.connections_statuses[channel.connection_id].get('last_ping') or now - \
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
            self.remove_channel(channel)

    def remove_channel(self, channel):
        self.channels_repository.delete(channel.connection_id)
        self.channels_cache.pop(channel.connection_id, None)
        self.connections_statuses.pop(channel.connection_id, None)
        self.remove_handlers(channel)
