#
# Github patch for PubSub
# https://github.com/aio-libs/aioredis/issues/439


import asyncio
import json
import pickle
import async_generator

import aioredis
import typing

import time


class PubSub:
    # pylint: disable=R0902, too-many-instance-attributes
    _TERMINATE = object()

    def __init__(self,
                 redis: aioredis.Redis,
                 serializer=pickle.dumps,
                 deserializer=pickle.loads) -> None:

        self.redis = redis
        self.serializer = serializer
        self.deserializer = deserializer

        self._lock = asyncio.Lock()
        self._mpsc = aioredis.pubsub.Receiver()
        self._reader_fut: typing.Optional[asyncio.Future] = None
        self._registry: typing.Dict[
            aioredis.abc.AbcChannel,
            typing.Set[asyncio.Queue],
        ] = {}

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
        # pylint: disable=E1102, not-callable
        serialized = self.serializer(message)
        await self.redis.publish(channel, serialized)

    @async_generator.asynccontextmanager
    async def _subscribe(self,
                         channel: str,
                         is_pattern: bool
                         ) -> typing.AsyncGenerator[asyncio.Queue, None]:
        """
        Async context manager that provides a multi-consumer proxy for aioredis'
        pubsub single-consumer.
        """
        async with self._lock:
            handler = self._mpsc.pattern if is_pattern else self._mpsc.channel
            registration = handler(channel)
            subscription: asyncio.Queue = asyncio.Queue()

            if registration not in self._registry:
                if is_pattern:
                    method, name = self.redis.psubscribe, 'pattern'
                else:
                    method, name = self.redis.subscribe, 'channel'

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
                        method, name = self.redis.punsubscribe, 'pattern'
                    else:
                        method, name = self.redis.unsubscribe, 'channel'

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


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    async def getsub():
        from core.src.world.builder import async_redis_data
        redis = await async_redis_data()
        ps = await PubSub(
            await redis,
            json.dumps,
            json.loads
        ).start()
        return ps

    async def unsubscribe(task):
        await asyncio.sleep(2)
        task.cancel()
        print('done')


    async def prova():
        try:
            sub = await getsub()
            async for x in sub.subscribe('prova'):
                print(x)
        finally:
            print('exited')

    task = loop.create_task(prova())
    loop.create_task(unsubscribe(task))
    loop.run_forever()


#if __name__ == '__main__':
#    loop = asyncio.get_event_loop()
#
#    async def getsub():
#        from core.src.world.builder import async_redis_data
#        redis = await async_redis_data()
#        ps = await PubSub(
#            await redis,
#            json.dumps,
#            json.loads
#        ).start()
#        return ps
#
#    async def pub():
#        i = 0
#        from core.src.world.builder import async_redis_data
#        r = await (await async_redis_data())
#        await asyncio.sleep(0)
#        ps = PubSub(
#            r,
#            json.dumps,
#            json.loads
#        )
#        i += 1
#        while 1:
#            await ps.publish('prova' + str(i % 30000), str(i % 30000))
#
#    async def sub():
#        s = time.time()
#        _i = 0
#
#        async def _sub(d):
#            nonlocal s
#            nonlocal _i
#            async for _x in ps.subscribe('prova' + str(d)):
#                assert _x == str(d)
#                _i += 1
#                if not _i % 10000:
#                    print('{} messages received in {}'.format(_i, time.time() - s))
#        ps = await getsub()
#
#        for x in range(0, 30000):
#            l.create_task(_sub(x))
#
#
#    l = asyncio.get_event_loop()
#    l.create_task(sub())
#    #l.create_task(pub())
#    #l.create_task(pub())
#    #l.create_task(pub())
#    #l.create_task(pub())
#    l.run_forever()
#