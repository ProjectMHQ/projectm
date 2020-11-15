import abc

import typing


class TransportInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def send(self, namespace, payload, topic):
        pass

    @abc.abstractmethod
    async def send_message(self, namespace, message):
        pass

    @abc.abstractmethod
    async def send_system_event(self, namespace, payload):
        pass


class SocketioTransportInterface(TransportInterface):
    def __init__(self, transport, messages_translator_strategy=None):
        self.transport = transport
        self.translator = messages_translator_strategy

    async def send_message(self, namespace, message: str):
        await self.send(namespace, message, 'msg')

    async def send_system_event(self, namespace, payload: typing.Dict):
        await self.send(namespace, payload, 'system')

    async def send(self, namespace, payload: (str, typing.Dict), topic):
        return await self.transport.emit(topic, payload, namespace='/{}'.format(namespace))
