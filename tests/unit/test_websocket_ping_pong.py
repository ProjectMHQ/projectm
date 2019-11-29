import asyncio
import random
import time
from unittest.mock import call, ANY, Mock

from core.src.auth.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.world.components import ComponentTypeEnum
from core.src.world.repositories.data_repository import RedisDataRepository
from core.src.world.services.transport.websocket_channels_service import WebsocketChannelsService
from etc import settings
import binascii
import os
import socketio

from tests.unit.bake_user import BakeUserTestCase


class TestWebsocketPingPong(BakeUserTestCase):

    def done(self):
        self.end = True

    async def async_test(self):
        sio = self.sio_client

        @sio.on('connect')
        async def connect(*a, **kw):
            await sio.emit(
                'create', {
                    'token': self._get_websocket_token('world:create'),
                    'name': 'Hero %s' % self.randstuff
                }
            )

        @sio.on('create')
        async def create(*a, **kw):
            for c in self._on_create:
                c(*a, **kw)

        await sio.connect('http://127.0.0.1:{}'.format(self.socketioport))
        s = int(time.time())
        while 1:
            if int(time.time()) - s > self.max_execution_time:
                raise TimeoutError('Max Execution time hit. Test started %s, now %s', s, int(time.time()))
            if self.end:
                print('End = True')
                break
            await asyncio.sleep(1)

    async def _do_auth(self, token):
        sio = self.sio_client

        @sio.on('auth')
        async def auth(*a, **kw):
            data = a[0]['data']
            self.assertEqual(data['character_id'], self._returned_character_id)
            self._private_channel_id = data['channel_id']
            assert binascii.unhexlify(self._private_channel_id), self._private_channel_id
            for c in self._on_auth:
                c(*a, **kw)

        await sio.emit(
            'auth', {
                'token': token
            }
        )

    def _checktype(self, a, b):
        if a.startswith('e:'):
            for k, v in b.items():
                if k == 1:
                    int(v)
        self.typeschecked = True

    def _check_on_create(self, resp):
        assert resp['success'], resp
        self._returned_character_id = resp['character_id']
        assert self._returned_character_id
        self.begin_auth_flow()

    def begin_auth_flow(self):
        auth_token = self._get_websocket_token('world:auth', character_id=self._returned_character_id)
        self.loop.create_task(self._do_auth(auth_token))

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
        self.loop = asyncio.get_event_loop()
        self.channels_factory = WebsocketChannelsRepository(self.redis)
        self.data_repository = RedisDataRepository(self.redis)
        self.redis_queue = asyncio.Queue()
        self.channels_monitor = WebsocketChannelsService(
            channels_repository=self.channels_factory,
            loop=self.loop,
            data_repository=self.data_repository,
            ping_interval=1,
            ping_timeout=10,
            redis_queue=self.redis_queue
        )

    def _base_flow(self, entity_id=1):
        self.current_entity_id = entity_id
        redis_eid = '{}'.format(entity_id).encode()
        self.redis.eval.side_effect = [redis_eid]
        self.redis.hget.side_effect = [None, redis_eid]
        self.redis.hmget.side_effect = ['Hero {}'.format(self.randstuff).encode()]
        self.redis.hscan_iter.side_effect = lambda *a, **kw: []
        self.redis.pipeline().hmset.side_effect = self._checktype
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

        @private.on('presence', namespace='/{}'.format(self._private_channel_id))
        async def presence(data):
            assert self._private_channel_id
            assert data == 'PING'
            await private.emit('presence', 'PONG', namespace='/{}'.format(self._private_channel_id))
            self._pings.append([int(time.time()), data])

        await private.connect(
            'http://127.0.0.1:{}'.format(self.socketioport), namespaces=['/{}'.format(self._private_channel_id)]
        )

    def _on_server_delete_channel(self, channel_id):
        assert channel_id == self._private_channel_id, (channel_id, self._private_channel_id)
        self._private_channel_id = None

    def _prepare_ping_pong(self, close_on_ping_pong_success=True):
        self.redis.hscan_iter.side_effect = self._hscan_iter_side_effect
        self.ping_pong_starts_at = int(time.time())
        self.channels_monitor.set_socketio_instance(self.sio_server)
        self.loop.create_task(self.channels_monitor.start())
        self.loop.create_task(self.do_ping_pong())
        close_on_ping_pong_success and self.loop.create_task(self.monitor_execution())

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
        return (x for x in ([
            ('c:{}'.format(self._private_channel_id).encode(),
             '{},{}'.format(self.current_entity_id, self.ping_pong_starts_at).encode())
        ] if self._private_channel_id else []))

    def test(self):
        self._private_channel_id = None
        self.redis.reset_mock()

        def _on_auth(*a, **kw):
            data = a[0]['data']
            self.assertEqual(data['character_id'], self._returned_character_id)
            self._private_channel_id = data['channel_id']
            self._prepare_ping_pong()

        self._on_auth = [_on_auth]
        self._base_flow(entity_id=random.randint(1, 9999))
        Mock.assert_called_with(self.redis.eval,
                                "\n            local val = redis.call('bitpos', 'e:m', 0)"
                                "\n            redis.call('setbit', 'e:m', val, 1)"
                                "\n            return val\n            ",
                                0)
        Mock.assert_called(self.redis.pipeline)
        Mock.assert_called(self.redis.pipeline().execute)
        Mock.assert_has_calls(
            self.redis.pipeline().setbit,
            any_order=True,
            calls=[
                call('c:2:m', self.current_entity_id, 1),
                call('c:1:m', self.current_entity_id, 1),
                call('c:5:m', self.current_entity_id, 1),
            ]
        )
        Mock.assert_has_calls(
            self.redis.pipeline().hmset,
            any_order=True,
            calls=[
                call('c:1:d', {self.current_entity_id: ANY}),
                call('c:2:d', {self.current_entity_id: 'Hero {}'.format(self.randstuff)}),
                call('e:{}'.format(self.current_entity_id), {
                    ComponentTypeEnum.CREATED_AT.value: ANY,
                    ComponentTypeEnum.NAME.value: 'Hero {}'.format(self.randstuff)
                })
            ]
        )
        Mock.assert_has_calls(
            self.redis.hget,
            calls=[
                call('char:e', self._returned_character_id),
                call('char:e', self._returned_character_id)
            ]
        )
        Mock.assert_has_calls(
            self.redis.hset,
            calls=[
                call('char:e', self._returned_character_id, self.current_entity_id),
                call('wschans', 'c:{}'.format(self._private_channel_id), ANY)
            ]
        )
        Mock.assert_called_with(self.redis.hscan_iter, 'wschans')
