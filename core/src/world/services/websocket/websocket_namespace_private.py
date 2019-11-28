import asyncio
import time
from socketio import AsyncNamespace

from core.src.auth.logging_factory import LOGGER


class PrivateNamespace(AsyncNamespace):
    def __init__(
            self, *a, redis_queue=None, channel=None, observer=None, ping_timeout=None, ping_interval=None, **kw
    ):
        super().__init__(*a, **kw)
        self.flood_rate = 0
        self.last_ping_sent = 0
        self.last_ping_received = 0
        self.last_pong_received = 0
        self.created_at = 0
        self.connected_at = 0
        self.disconnected_at = 0
        self.connected = False
        self.redis_queue = redis_queue
        self.channel = channel
        self.observer = observer
        self.ping_timeout = ping_timeout
        self.ping_interval = ping_interval
        self.sid = None

    async def on_connect(self, sid, data):
        LOGGER.websocket_monitor.debug(
            'Session %s connected to channel %s (entity %s)', sid, self.channel.id, self.channel.entity_id
        )
        if self.sid and self.sid != sid:
            await self.disconnect(self.sid)
        self.sid = sid

        self.connected = True
        self.connected_at = int(time.time())
        await self.redis_queue.put(
            {
                'n': self.channel.id,
                'e_id': self.channel.entity_id,
                't': int(time.time()),
                'c': 'connected'
            }
        )
        await self.ping()
        await self.observer.on_connect(self.channel)

    async def on_disconnect(self, sid):
        self.connected = False
        self.disconnected_at = int(time.time())
        await self.redis_queue.put({
                'n': self.channel.id,
                'e_id': self.channel.entity_id,
                't': int(time.time()),
                'c': 'disconnected'
            }
        )
        await self.observer.on_disconnect(self.channel)

    async def on_cmd(self, _, data):

        await self.redis_queue.put(
            {
                'n': self.channel.id,
                'e_id': self.channel.entity_id,
                'd': data,
                't': int(time.time()),
                'c': 'cmd'
            }
        )
        await self.observer.on_cmd(self.channel, data)

    async def on_presence(self, _, data):
        if data == 'PING':
            LOGGER.websocket_monitor.debug(
                'Received PING for channel %s (entity %s)', self.channel.id, self.channel.entity_id
            )
            now = int(time.time())
            if now - self.last_ping_received < (self.ping_interval - (self.ping_interval*0.1)):
                self.flood_rate += 1
                if self.flood_rate == 5:
                    await self.emit('presence', 'EXCESS FLOOD')
                    await self.emit('msg', {"event": "disconnect", "reason": "excess_flood"})
                    await self.disconnect(self.sid)
                    await self.observer.on_close(self.channel, reason="flood")

            self.last_ping_received = int(time.time())
            await self.emit('presence', 'PONG')
            await self.observer.on_ping_received(self.channel)

        elif data == 'PONG':
            LOGGER.websocket_monitor.debug(
                'Received PONG for channel %s (entity %s)', self.channel.id, self.channel.entity_id
            )
            self.last_pong_received = int(time.time())
            await self.observer.on_pong_received(self.channel)

    async def ping(self):
        LOGGER.websocket_monitor.debug(
            'Sending PING on channel %s (entity %s)', self.channel.id, self.channel.entity_id
        )
        await self.emit('presence', 'PING')
        self.last_ping_sent = int(time.time())
        await self.observer.on_ping_sent(self.channel)

    async def do_concurrency_close(self):
        LOGGER.websocket_monitor.debug(
            'Closing channel due concurrency. Channel %s (entity %s)', self.channel.id, self.channel.entity_id
        )
        await self.emit('msg', {"event": "disconnect", "reason": "concurrency"})
        await self.disconnect(self.sid)
        await self.observer.on_close(self.channel, reason="concurrency")

    async def monitor(self):
        LOGGER.websocket_monitor.debug(
            'Monitoring channel %s (entity %s)', self.channel.id, self.channel.entity_id
        )
        now = int(time.time())
        if now - self.last_ping_sent >= (self.ping_interval - self.ping_interval * 0.1):
            if self.connected:
                await self.ping()

        ping_timeout = False
        if self.last_pong_received:
            if now - self.last_pong_received > self.ping_timeout:
                ping_timeout = True
        else:
            if now - self.channel.created_at > self.ping_timeout:
                ping_timeout = True

        if ping_timeout:
            LOGGER.websocket_monitor.debug(
                'PING TIMEOUT on channel %s (entity %s)', self.channel.id, self.channel.entity_id
            )
            await self.emit('presence', 'PING TIMEOUT')
            await self.emit('msg', {"event": "disconnect", "reason": "ping_timeout"})
            await self.disconnect(self.sid)
            await self.observer.on_close(self.channel, reason="timeout")
        else:
            await asyncio.sleep(self.ping_interval)
            asyncio.ensure_future(self.monitor())


def private_namespace_factory(
        _redis_queue,
        _channel,
        _observer,
        _ping_timeout,
        _ping_interval
) -> PrivateNamespace:

    return PrivateNamespace(
        '/{}'.format(_channel.id),
        redis_queue=_redis_queue,
        channel=_channel,
        observer=_observer,
        ping_timeout=_ping_timeout,
        ping_interval=_ping_interval
    )
