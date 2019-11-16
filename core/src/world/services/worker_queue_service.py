import asyncio
from core.src.world.services.redis_queue import RedisQueueConsumer


class WorkerQueueService:
    """
    This ensure messages from the same "entity_id" are processed in order.
    """
    def __init__(self, loop, consumer):
        self.consumer = consumer
        self._queues = {}
        self.loop = loop
        self.messages_observers = {}

    def add_queue_observer(self, context, observer):
        if not self.messages_observers.get(context):
            self.messages_observers[context] = []
        self.messages_observers[context].append(observer)

    async def _process_queue(self, entity_id: str):
        try:
            msg = self._queues[entity_id].get_nowait()
            self.messages_observers.get(msg['c']) and await asyncio.gather(
                *(o.on_message(msg) for o in self.messages_observers[msg['c']])
            )
            await self._process_queue(entity_id)
            """
            When a buffer of messages is received, the process_queue is
            called until the message queue is exhaust. 
            """
        except asyncio.QueueEmpty:
            assert self._queues.pop(entity_id).empty()
            pass

    async def run(self):
        while 1:
            msg = await self.consumer.get()
            try:
                self._queues[msg['e_id']].put_nowait(msg)
                continue
            except KeyError:
                self._queues[msg['e_id']] = asyncio.Queue()
                self._queues[msg['e_id']].put_nowait(msg)
                self.loop.create_task(self._process_queue(msg['e_id']))
