import typing

from core.src.auth.logging_factory import LOGGER
from etc import settings
from core.src.world.domain.entity import Entity, EntityID
from core.src.world.utils.world_types import Transport


class CommandsObserver:
    def __init__(self, transport):
        self._commands = {}
        self.transport = transport

    def add_command(self, method: callable, *aliases: str):
        for alias in aliases:
            self._commands[alias] = method

    async def on_message(self, message: typing.Dict):
        assert message['c'] == 'cmd'
        try:
            data = message['d'].strip().split(' ')
            if not data:
                raise TypeError('Empty command?')

            entity = Entity(EntityID(message['e_id']), transport=Transport(message['n'], self.transport))
            command = self._commands[data[0].lower()]
            if getattr(command, 'get_self', False):
                await self._commands[data[0]](entity, *data)
            else:
                await self._commands[data[0]](entity, *data[1:])
        except KeyError as exc:
            if settings.RUNNING_TESTS:
                raise
            await self._on_error(message, "Command not found: %s" % data[0])
            LOGGER.core.exception('Unhandled exception %s', exc)
        except TypeError as exc:
            if settings.RUNNING_TESTS:
                raise
            await self._on_error(message, "Command error: %s" % str(exc))
            LOGGER.core.exception('Unhandled exception %s', exc)
        except Exception as exc:
            LOGGER.core.exception('Unhandled exception %s', exc)
            print(exc)

    def _on_error(self, message, error):
        return self.transport.send_system_event(namespace=message['n'], payload={"event": "cmd", "error": error})
