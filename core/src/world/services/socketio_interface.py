import abc


class TransportInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def send(self, namespace, payload, topic='msg'):
        pass


class SocketioTransportInterface(TransportInterface):
    def __init__(self, transport):
        self.transport = transport

    async def send(self, namespace, payload, topic='msg'):
        print('sending on namespace %s, topic %s, payload %s' % (namespace, topic, payload))
        return await self.transport.emit(topic, payload, namespace='/{}'.format(namespace))
