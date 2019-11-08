import time


class CommandsSystem:
    def __init__(
            self,
            redis_queues_manager,
            channels_service,
    ):
        self.redis_queues_manager = redis_queues_manager
        self.channels_service = channels_service
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    async def on_message(self, namespace: str, entity_id: int, message: str):
        await self.redis_queues_manager.put(
            namespace,
            {'n': namespace, 'e_id': entity_id, 'd': message, 't': int(time.time())}
        )
