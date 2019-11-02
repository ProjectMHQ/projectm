from unittest import TestCase


class TestWebsocketCharacterAuthentication(TestCase):
    def test_character_create_and_auth(self):
        ping_timeout = 5
        self.run_websocket_server(ping_interval=2, ping_timeout=ping_timeout)
        user = self._create_user('user@email.com', 'password')
        ws_cli = self._get_websocket_client(user)
        public = ws_cli.connect('/')
        character_id = public.create(name="Hero")
        channel_id = public.authenticate(character_id)
        private = ws_cli.connect('/' + channel_id)
        pings_container = []
        private.on_event('presence', lambda x: pings_container.append(x))
        self._wait_for_disconnection(private, max_wait_time=ping_timeout + 1)
        self.assertEqual(pings_container, 2)

