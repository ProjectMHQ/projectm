import asyncio
import unittest
import binascii
import os
from tests.bake_user import BakeUserTestCase


class TestWebsocketCharacterAuthentication(BakeUserTestCase):
    def setUp(self):
        self.connected = False
        self.socketioport = 12349

    async def async_test(self):
        import socketio
        sio = socketio.AsyncClient()

        @sio.on('connect')
        async def connect(*a, **kw):
            await sio.emit(
                'create', {
                    'token': self._get_websocket_token('world:create'),
                    'name': 'Hero %s' % binascii.hexlify(os.urandom(8))
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

    def test(self):
        self._bake_user()
        self._run_test()


if __name__ == '__main__':
    unittest.main()
