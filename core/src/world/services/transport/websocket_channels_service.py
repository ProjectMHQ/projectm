import asyncio

import time

from core.src.auth.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.auth.logging_factory import LOGGER
from core.src.world.services.transport.websocket_namespace_private import private_namespace_factory


class WebsocketChannelsService:
    def __init__(
            self,
            socketio=None,
            channels_repository: WebsocketChannelsRepository=None,
            loop=None,
            data_repository=None,
            redis_queue=None,
            ping_interval=15,
            ping_timeout=35
    ):
        self.loop = loop
        self.connections_statuses = {}
        self.socketio = socketio
        self.channels_repository = channels_repository
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.data_repository = data_repository
        self._on_delete_channel_observers = []
        self._on_ping_observers = []
        self._on_pong_observers = []
        self._on_cmd_observers = []
        self._on_disconnect_observers = []
        self._on_connect_observers = []
        self._on_new_channel_observers = []
        self._pending_channels = asyncio.Queue()
        self.redis_queues_manager = redis_queue
        self.active_namespaces = {}
        self.channels_by_entity_id = {}

    def set_socketio_instance(self, sio):
        self.socketio = sio
        return self

    def set_event_loop(self, loop):
        self.loop = loop
        return self

    def add_on_channel_delete_observer(self, observer):
        self._on_delete_channel_observers.append(observer)

    def add_on_ping_observer(self, observer):
        self._on_ping_observers.append(observer)

    def add_on_disconnect_observer(self, observer):
        self._on_disconnect_observers.append(observer)

    def add_on_connect_observer(self, observer):
        self._on_connect_observers.append(observer)

    def add_on_cmd_observer(self, observer):
        self._on_cmd_observers.append(observer)

    def add_on_new_channel_observer(self, observer):
        self._on_new_channel_observers.append(observer)

    async def start(self):
        await self.bootstrap_server()
        while 1:
            channel = await self._pending_channels.get()
            self.loop.create_task(self._activate_pending_channel(channel))
            await asyncio.sleep(0.01)

    async def bootstrap_server(self):
        channels = list(self.channels_repository.get_active_channels())
        LOGGER.websocket_monitor.debug('Monitoring %s', channels)
        await asyncio.gather(
            *(self._activate_pending_channel(channel) for channel in channels)
        )

    async def enable_channel(self, channel):
        self._pending_channels.put_nowait(channel)

    async def _activate_pending_channel(self, channel):
        if '/{}'.format(channel.id) in self.socketio.namespace_handlers:
            raise ValueError('Channel already activated')

        now = int(time.time())
        if now - self.ping_timeout > channel.created_at:
            self.channels_repository.delete(channel.id)
            for observer in self._on_delete_channel_observers:
                self.loop.create_task(observer.on_event(channel))

        elif '/{}'.format(channel.id) not in self.socketio.namespace_handlers:
            await self._close_other_namespaces_for_entity(channel)
            await self.activate_namespace(channel)
            for observer in self._on_new_channel_observers:
                self.loop.create_task(observer.on_event(channel))

    async def _close_other_namespaces_for_entity(self, channel):
        if channel.entity_id in self.channels_by_entity_id:
            namespace = self.socketio.namespace_handlers[
                '/{}'.format(self.channels_by_entity_id[channel.entity_id])
            ]
            await namespace.do_concurrency_close()

    async def close_namespace_for_entity_id(self, entity_id):
        if entity_id in self.channels_by_entity_id:
            namespace = self.socketio.namespace_handlers[
                '/{}'.format(self.channels_by_entity_id[entity_id])
            ]
            await namespace.do_close()

    async def activate_namespace(self, channel):
        namespace = private_namespace_factory(
            self.redis_queues_manager,
            channel,
            self._channel_observers_interface(),
            self.ping_timeout,
            self.ping_interval
        )
        self.socketio.register_namespace(namespace)
        self.loop.create_task(namespace.monitor())
        self.channels_by_entity_id[channel.entity_id] = channel.id

    async def _on_close(self, channel, reason):
        self.socketio.namespace_handlers.pop('/{}'.format(channel.id), None)
        self.channels_repository.delete(channel.id)

        if channel.id == self.channels_by_entity_id.get(channel.entity_id):
            self.channels_by_entity_id.pop(channel.entity_id, None)

        for observer in self._on_delete_channel_observers:
            self.loop.create_task(observer.on_event(channel))

    def _channel_observers_interface(self):

        class _Observer:
            @staticmethod
            async def on_connect(channel):
                for handler in self._on_connect_observers:
                    self.loop.create_task(handler.on_connect(channel))

            @staticmethod
            async def on_disconnect(channel):
                for handler in self._on_disconnect_observers:
                    self.loop.create_task(handler.on_event(channel))

            @staticmethod
            async def on_ping_sent(channel):
                for handler in self._on_ping_observers:
                    self.loop.create_task(handler.on_event(channel))

            @staticmethod
            async def on_ping_received(channel):
                pass

            @staticmethod
            async def on_pong_received(channel):
                for handler in self._on_pong_observers:
                    self.loop.create_task(handler.on_event(channel))

            @staticmethod
            async def on_cmd(channel, data):
                for handler in self._on_cmd_observers:
                    self.loop.create_task(handler.on_cmd(channel, data))

            @staticmethod
            async def on_close(channel, reason=None):
                self.loop.create_task(self._on_close(channel, reason))

        return _Observer()
