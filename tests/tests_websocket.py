import hashlib
import json
import unittest
import binascii
import os
import uuid

from flask_testing import TestCase
from gevent import threading

import socketIO_client


class TestWebsocketCharacterAuthentication(TestCase):
    socketio = None
    socketioport = 13254

    def create_app(self):
        from core.app import app
        self.app = app
        return app

    def _create_user(self, email, password):
        response = self.client.post('/auth/signup', data=json.dumps({'email': email, 'password': password}))
        self.assert200(response)
        self.assertEqual(response.data, b'SIGNUP_CONFIRMED')

    def _auth_user(self, email, password):
        response = self.client.post('/auth/login', data=json.dumps({'email': email, 'password': password}))
        self.assert200(response)
        user = uuid.UUID(response.json['user_id'])
        t = response.headers['Set-Cookie'].replace('Authorization=', '').replace('Bearer ', '').split(';')
        return user, t[0].strip('"').strip(' ')

    def _run_websocket_server(self):
        from core.app import socketio

        def _d():

            self.socketio = socketio
        self.socketio_thread = threading.Thread(target=_d, daemon=True)
        self.socketio_thread.start()


    def test(self):
        ping_timeout = 5
        email = binascii.hexlify(os.urandom(8)).decode() + '@tests.com'
        password = hashlib.sha256(b'password').hexdigest()
        self._create_user(email, password)
        user_id, auth_token = self._auth_user(email, password)
        self._run_websocket_server()
        with socketIO_client.SocketIO(
                '127.0.0.1', self.socketioport, headers={'Authorization': 'Bearer %s' % auth_token}
        ) as ws:
            ws.connect('/')

        exit()


if __name__ == '__main__':
    unittest.main()
