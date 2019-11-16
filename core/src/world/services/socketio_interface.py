import abc


class TransportInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def emit(self, namespace, topic, payload):
        pass


class SocketioTransportInterface(TransportInterface):
    def __init__(self, transport):
        self.transport = transport

    async def emit(self, namespace, topic, payload):
        return await self.transport.emit(topic, payload, namespace='/{}'.format(namespace))
