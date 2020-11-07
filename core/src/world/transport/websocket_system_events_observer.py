from core.src.world.services.redis_pubsub_publisher_service import PubSubEventType


class TransportSystemEventsObserver:
    def __init__(self):
        self.transport_service = None

    def add_transport_service(self, transport_service):
        self.transport_service = transport_service

    async def on_event(self, topic, message):
        if message['ev'] == PubSubEventType.ENTITY_QUIT.value:
            await self.transport_service.close_namespace_for_entity_id(message['en'])
