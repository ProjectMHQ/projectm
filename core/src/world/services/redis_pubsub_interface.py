#
# Github patch for PubSub
# https://github.com/aio-libs/aioredis/issues/439


import asyncio
import json
import async_generator

import aioredis
import typing

import time


class PubSubManager:
    # pylint: disable=R0902, too-many-instance-attributes
    _TERMINATE = "EXTERMINATE"

    def __init__(self,
                 redis: callable,
                 serializer=json.dumps,
                 deserializer=json.loads) -> None:

        self._redis_factory = redis
        self.serializer = serializer
        self.deserializer = deserializer

        self._lock = asyncio.Lock()
        self._mpsc = aioredis.pubsub.Receiver()
        self._reader_fut: typing.Optional[asyncio.Future] = None
        self._registry: typing.Dict[
            aioredis.abc.AbcChannel,
            typing.Set[asyncio.Queue],
        ] = {}
        self._redis = None
        
    async def redis(self) -> aioredis.Redis:
        if not self._redis:
            self._redis = await self._redis_factory()
        return self._redis

    async def start(self):
        self._reader_fut = asyncio.ensure_future(self.reader())
        return self

    async def stop(self) -> None:
        if not self._reader_fut:
            raise RuntimeError(f'{type(self).__name__} is not running.')
        self._reader_fut.cancel()
        cancellation_fut = asyncio.gather(*[
            subscription.put(self._TERMINATE)
            for subscriptions in self._registry.values()
            for subscription in subscriptions
        ])
        cancellation_fut.add_done_callback(lambda fut: self.stop)

    async def reader(self):
        async for channel, produced in self._mpsc.iter():
            channel = typing.cast(aioredis.abc.AbcChannel, channel)

            try:
                data = produced[1] if channel.is_pattern else produced
                message = self.deserializer(data)
            except Exception:   # pylint: disable=W0703, broad-except
                continue

            asyncio.gather(*[
                sub.put(message)
                for sub in self._registry.get(channel, [])
            ])

    async def publish(self, channel, message):
        redis = await self.redis()
        # pylint: disable=E1102, not-callable
        serialized = self.serializer(message)
        await redis.publish(channel, serialized)

    @async_generator.asynccontextmanager
    async def _subscribe(self,
                         channel: str,
                         is_pattern: bool
                         ) -> typing.AsyncGenerator[asyncio.Queue, None]:
        """
        Async context manager that provides a multi-consumer proxy for aioredis'
        pubsub single-consumer.
        """
        redis = await self.redis()
        async with self._lock:
            handler = self._mpsc.pattern if is_pattern else self._mpsc.channel
            registration = handler(channel)
            subscription: asyncio.Queue = asyncio.Queue()

            if registration not in self._registry:
                if is_pattern:
                    method, name = redis.psubscribe, 'pattern'
                else:
                    method, name = redis.subscribe, 'channel'

                await method(registration)
                self._registry[registration] = set()
            self._registry[registration].add(subscription)

        try:
            yield subscription
        finally:
            async with self._lock:
                self._registry[registration].remove(subscription)
                if not self._registry[registration]:
                    if is_pattern:
                        method, name = redis.punsubscribe, 'pattern'
                    else:
                        method, name = redis.unsubscribe, 'channel'

                    await method(registration)
                    del self._registry[registration]

    async def subscribe(self,
                        channel: str,
                        is_pattern: bool = False,
                        ) -> typing.AsyncGenerator[typing.Any, None]:
        # pylint: disable=E1701, not-async-context-manager
        async with self._subscribe(channel, is_pattern) as subscription:
            while True:
                value = await subscription.get()
                if value is self._TERMINATE:
                    break
                else:
                    yield value
