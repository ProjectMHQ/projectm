import asyncio
import random
import time
from unittest import mock
from core.src.auth.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.world.repositories.data_repository import RedisDataRepository
from core.src.world.services.transport.websocket_channels_service import WebsocketChannelsService
from etc import settings
import binascii
import os
import socketio
from tests.unit._test_websocket_character_create_auth import BaseWSFlowTestCase
from core.src.world.builder import websocket_channels_service


class TestWebsocketPingPongFailed(BaseWSFlowTestCase):
    """
    small integration test for websocket flow. redis mocked.
    """
    def setUp(self):
        assert settings.RUNNING_TESTS
        self.connected = False
        self.socketioport = random.randint(10000, 50000)
        self.randstuff = binascii.hexlify(os.urandom(8)).decode()
        self.typeschecked = False
        self.sio_client = socketio.AsyncClient()
        self._on_create = []
        self._on_auth = []
        self.end = False
        self._private_channel_id = None
        self._engaged_private_channel_id = None
        self.max_execution_time = 55
        self._pings = []
        self.wasconnected = False
        self._expected_pings = 1
        self.loop = asyncio.get_event_loop()
        self.channels_factory = mock.create_autospec(WebsocketChannelsRepository)
        self.data_repository = mock.create_autospec(RedisDataRepository)
        self.redis_queue = asyncio.Queue()
        self.channels_monitor = WebsocketChannelsService(
            channels_repository=self.channels_factory,
            loop=self.loop,
            data_repository=self.data_repository,
            ping_interval=1,
            ping_timeout=5,
            redis_queue=self.redis_queue
        )
        self.loop.set_debug(True)
        self.channels_monitor._pending_channels = websocket_channels_service._pending_channels

    def _base_flow(self, entity_id=1):
        self.current_entity_id = entity_id
        self._bake_user()
        self._on_create.append(self._check_on_create)
        self._run_test()
        self.assertTrue(self.typeschecked)

    async def do_ping_pong(self):
        private = socketio.AsyncClient()
        self.private = private

        @private.on('connect', namespace='/{}'.format(self._private_channel_id))
        async def connect():
            print('Connected to private namespace /{}'.format(self._private_channel_id))
            self.loop.create_task(self.monitor_execution())

        @private.on('presence', namespace='/{}'.format(self._private_channel_id))
        async def presence(data):
            if not self.ping_timeout:
                assert data == 'PING'
            else:
                assert data in ('PING', 'PING TIMEOUT')
            self._pings.append([int(time.time()), data])

        await private.connect(
            'http://127.0.0.1:{}'.format(self.socketioport),
            namespaces=['/{}'.format(self._private_channel_id)],
        )
        self._engaged_private_channel_id = self._private_channel_id

    def _on_server_delete_channel(self):

        class Observer:
            @staticmethod
            async def on_event(channel):
                print('SERVER DELETE CHANNEL ', channel.id)
                assert channel.id == self._engaged_private_channel_id
                self._engaged_private_channel_id = None
        return Observer()

    def _on_ping_event(self):

        class Observer:
            @staticmethod
            async def on_event(channel):
                assert channel.id == self._engaged_private_channel_id
                self._expected_pings += 1
        return Observer()

    def _prepare_ping_pong(self):
        self.ping_pong_starts_at = int(time.time())
        self.channels_monitor.add_on_channel_delete_observer(self._on_server_delete_channel())
        self.channels_monitor.add_on_ping_observer(self._on_ping_event())
        self.channels_monitor.set_socketio_instance(self.sio_server)
        self.loop.create_task(self.channels_monitor.start())
        self.loop.create_task(self.do_ping_pong())

    async def monitor_execution(self):
        while 1:
            self.wasconnected = self.wasconnected or self.private.connected
            await asyncio.sleep(0.1)
            if self.wasconnected and not self._engaged_private_channel_id:
                self.done()
                break

    def _hscan_iter_side_effect(self, p):
        """
        hscan for get channels
        """
        assert p == 'wschans', p
        return (x for x in ([
            ('c:{}'.format(self._engaged_private_channel_id).encode(),
             '{},{}'.format(self.current_entity_id, self.ping_pong_starts_at).encode())
        ] if self._engaged_private_channel_id else []))

    def test(self):
        self.ping_timeout = True

        def _on_auth(*a, **kw):
            data = a[0]['data']
            self.assertEqual(data['character_id'], self._returned_character_id)
            self._private_channel_id = data['channel_id']
            self._prepare_ping_pong()

        self._on_auth = [_on_auth]
        self._base_flow(entity_id=random.randint(1, 9999))
        self.assertEqual(
            len(self._pings),
            self._expected_pings,
            msg="{} {}".format(len(self._pings), self._expected_pings)
        )
