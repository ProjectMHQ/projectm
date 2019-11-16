import typing

from core.src.world.entity import Entity, EntityID
from core.src.world.world_types import Transport


class CommandsObserver:
    def __init__(self, transport):
        self._commands = {}
        self.transport = transport

    def add_command(self, command: str, method: callable):
        self._commands[command] = method

    async def on_message(self, message: typing.Dict):
        assert message['c'] == 'cmd'
        try:
            data = message['d'].strip().split(' ')
            if not data:
                raise TypeError('Empty command?')

            entity = Entity(EntityID(message['e_id']), transport=Transport(message['n'], self.transport))
            await self._commands[data[0]](entity, *data[1:])
            print('asdf')
        except KeyError:
            await self._on_error(message, "Command not found: %s" % data[0])
        except TypeError as exc:
            await self._on_error(message, "Command error: %s" % str(exc))

    def _on_error(self, message, error):
        return self.transport.send(namespace=message['n'], payload={"event": "cmd", "error": error})
