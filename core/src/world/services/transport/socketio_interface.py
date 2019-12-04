import abc


class TransportInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def send(self, namespace, payload, topic='msg'):
        pass


class SocketioTransportInterface(TransportInterface):
    def __init__(self, transport, messages_translator_strategy=None):
        self.transport = transport
        self.translator = messages_translator_strategy

    async def send(self, namespace, payload, topic='msg'):
        if self.translator:
            payload = self.translator.payload_msg_to_string(payload, topic)
        return await self.transport.emit(topic, payload, namespace='/{}'.format(namespace))
