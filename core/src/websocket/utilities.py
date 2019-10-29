import typing
from functools import wraps

from core.src.websocket.types import WebsocketContext


def ws_commands_extractor(data: str):
    if not data:
        return '', []
    _s = [x for x in data.strip().split(' ') if x]
    if len(_s) > 1:
        return _s[0], _s[1:]
    return _s[0], []


class WSCommandsInterfaceFactory:
    def __init__(self):
        self._contexts = {}

    def add_interface(self, factory):
        self._contexts[factory.ctx] = factory

    def __getattr__(self, name):
        return self._contexts[name]

    def get_interface(self, name: str, topic: str):
        ctx = WebsocketContext(name)
        return self._contexts[ctx]


def deserialize_message(deserializer):
    def _fn(fun):
        @wraps(fun)
        def wrapper(a, **kw):
            fun(deserializer(a), **kw)
        return wrapper
    return _fn


def ensure_topic_exists(fun):
    @wraps(fun)
    def wrapper(message: typing.Dict, **kw):

        fun(message, **kw)
    return wrapper
