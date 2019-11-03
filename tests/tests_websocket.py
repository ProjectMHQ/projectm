from unittest.mock import call, ANY

from etc import settings
import asyncio
import unittest
import binascii
import os
from tests.bake_user import BakeUserTestCase


class TestWebsocketCharacterAuthentication(BakeUserTestCase):
    """
    small integration test for websocket flow. redis mocked.
    """
    def setUp(self):
        assert settings.RUNNING_TESTS
        self.connected = False
        self.socketioport = 12349
        self.randstuff = binascii.hexlify(os.urandom(8)).decode()
        self.typeschecked = False

    async def async_test(self):

        import socketio
        sio = socketio.AsyncClient()

        @sio.on('connect')
        async def connect(*a, **kw):
            await sio.emit(
                'create', {
                    'token': self._get_websocket_token('world:create'),
                    'name': 'Hero %s' % self.randstuff
                }
            )

        @sio.on('auth')
        async def auth(*a, **kw):
            raise ValueError('auth response HERE')

        @sio.on('msg')
        async def msg(*data):
            print(data)

        await sio.connect('http://127.0.0.1:{}'.format(self.socketioport))
        await asyncio.sleep(1)

    def _checktype(self, a, b):
        print('Checking types: %s' % b)
        if a.startswith('e:'):
            for k, v in b.items():
                if k == 1:
                    int(v)
        self.typeschecked = True

    def test(self):
        self.redis.eval.side_effect = [b'1']
        self.redis.hget.side_effect = [None, ]
        self.redis.pipeline().hmset.side_effect = self._checktype
        self._bake_user()
        self._run_test()
        self.redis.assert_has_calls(
            [call.setbit('e:m', 0, 1),
             call.eval(
                 "\n            local val = redis.call('bitpos', 'e:m', 0)\n            redis.call('setbit', 'e:m', val, 1)\n            return val\n            ",
                 0),
             call.pipeline(),
             call.pipeline().hmset('e:1', {2: "Hero %s" % self.randstuff, 1: ANY}),
             call.pipeline().setbit('c:2:m', 1, True),
             call.pipeline().hmset('c:2:d', {1: "Hero %s" % self.randstuff}),
             call.pipeline().setbit('c:1:m', 1, True),
             call.pipeline().hmset('c:1:d', {1: ANY}),
             call.pipeline().execute(),
             call.hmget('e:1', ANY),
             call.hget('char:e', ANY),
             call.hset('char:e', ANY, 1)]
        )
        self.assertTrue(self.typeschecked)


if __name__ == '__main__':
    unittest.main()
