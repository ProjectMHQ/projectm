import asyncio
import random
import time
from core.scripts.monitor_websocket_channels import builder
from etc import settings
import binascii
import os
import socketio
from tests.test_websocket_character_create_auth import TestWebsocketCharacterAuthentication


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
        self.max_execution_time = 55
        self._pings = []

    async def do_ping_pong(self):
        private = socketio.AsyncClient()
        self.private = private

        @private.on('connect', namespace='/{}'.format(self._private_channel_id))
        async def connect():
            print('Connected to private namespace /{}'.format(self._private_channel_id))

        @private.on('presence', namespace='/{}'.format(self._private_channel_id))
        async def presence(data):
            assert data == 'PING'
            await private.emit('presence', 'PONG', namespace='/{}'.format(self._private_channel_id))
            self._pings.append([int(time.time()), data])

        await private.connect(
            'http://127.0.0.1:{}'.format(self.socketioport), namespaces=['/{}'.format(self._private_channel_id)]
        )

    def _prepare_ping_pong(self):
        self.ping_pong_starts_at = int(time.time())
        ws_channels_monitor = builder(self.sio_server, redis_data=self.redis, ping_interval=1, ping_timeout=3)
        self.loop.create_task(ws_channels_monitor.start())
        self.loop.create_task(self.do_ping_pong())
        self.loop.create_task(self.monitor_execution())

    async def monitor_execution(self):
        while 1:
            await asyncio.sleep(1)
            if len(self._pings) == 5:
                self.done()

    def _hscan_iter_side_effect(self, p):
        """
        hscan for get channels
        """
        assert p == 'wschans', p
        return (x for x in [
            ('c:{}'.format(self._private_channel_id).encode(),
             '{},{}'.format(self.current_entity_id, self.ping_pong_starts_at).encode())
        ])

    def test(self):
        self.redis.reset_mock()
        self.redis.hscan_iter.side_effect = self._hscan_iter_side_effect
        self._on_auth.append(lambda *a, **kw: self._prepare_ping_pong())
        self._base_flow(entity_id=random.randint(1, 9999))
