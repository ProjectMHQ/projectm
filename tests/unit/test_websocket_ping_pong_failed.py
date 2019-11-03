import asyncio
import random
import time
from unittest.mock import Mock

from core.scripts.monitor_websocket_channels import builder
from etc import settings
import binascii
import os
import socketio
from tests.unit.test_websocket_character_create_auth import TestWebsocketCharacterAuthentication


class TestWebsocketPingPong(TestWebsocketCharacterAuthentication):
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
        self.channels_monitor_redis = Mock()
        self._expected_pings = 0

    async def do_ping_pong(self):
        private = socketio.AsyncClient()
        self.private = private

        @private.on('connect', namespace='/{}'.format(self._private_channel_id))
        async def connect():
            print('Connected to private namespace /{}'.format(self._private_channel_id))
            self.loop.create_task(self.monitor_execution())

        @private.on('presence', namespace='/{}'.format(self._private_channel_id))
        async def presence(data):
            assert data == 'PING'
            self._pings.append([int(time.time()), data])

        await private.connect(
            'http://127.0.0.1:{}'.format(self.socketioport),
            namespaces=['/{}'.format(self._private_channel_id)],
        )
        self._engaged_private_channel_id = self._private_channel_id

    def _on_server_delete_channel(self, channel_id):
        print('SERVER DELETE CHANNEL ', channel_id)
        assert channel_id == self._engaged_private_channel_id
        self._engaged_private_channel_id = None

    def _on_ping_event(self, channel_id):
        assert channel_id == self._engaged_private_channel_id
        self._expected_pings += 1

    def _prepare_ping_pong(self):
        self.ping_pong_starts_at = int(time.time())
        ws_channels_monitor = builder(
            self.sio_server, redis_data=self.channels_monitor_redis, ping_interval=1, ping_timeout=5
        )
        ws_channels_monitor.add_on_channel_delete_event(self._on_server_delete_channel)
        ws_channels_monitor.add_on_ping_event(self._on_ping_event)
        self.loop.create_task(ws_channels_monitor.start())
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
        self.redis.reset_mock()
        self.channels_monitor_redis.hscan_iter.side_effect = self._hscan_iter_side_effect
        self._on_auth.append(lambda *a, **kw: self._prepare_ping_pong())
        self._base_flow(entity_id=random.randint(1, 9999))
        self.assertEqual(len(self._pings), self._expected_pings)
