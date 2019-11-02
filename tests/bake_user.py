from aiohttp.web import _run_app
import asyncio
import hashlib
import json
import unittest
import binascii
import os
import uuid
from flask_testing import TestCase


class BakeUserTestCase(TestCase):
    socketio = None
    socketioport = 13254
    loop = asyncio.get_event_loop()
    ping_timeout = 60
    ping_interval = 30

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
        self.login_response = response
        self.assert200(response)
        user = uuid.UUID(response.json['user_id'])
        t = response.headers['Set-Cookie'].replace('Authorization=', '').replace('Bearer ', '').split(';')
        return user, t[0].strip('"').strip(' ')

    def _bake_user(self):
        email = binascii.hexlify(os.urandom(8)).decode() + '@tests.com'
        password = hashlib.sha256(b'password').hexdigest()
        self._create_user(email, password)
        self.user_id, self.auth_token = self._auth_user(email, password)

    def _run_test(self):
        self.loop.create_task(self._run_websocket_server())
        self.loop.run_until_complete(self.async_test())

    async def _run_websocket_server(self):
        from core.scripts.serve_websocket import app
        self.loop.create_task(_run_app(app, host='127.0.0.1', port=self.socketioport))

    def _get_websocket_token(self, context, character_id=None):
        payload = {'context': context}
        if character_id:
            payload['character_id'] = character_id
        response = self.client.post('/auth/token', data=json.dumps(payload), headers={
            'Authorization': 'Bearer {}'.format(self.auth_token)
        })
        self.assert200(response)
        return response.json['token']

    async def async_test(self):
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()
