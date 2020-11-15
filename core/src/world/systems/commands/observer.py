import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.system import SystemComponent

from etc import settings
from core.src.world.domain.entity import Entity


class CommandsObserver:
    def __init__(self, transport):
        self._commands = {}
        self.transport = transport
        self._enabled_channels = set()

    def enable_channel(self, channel_id):
        self._enabled_channels.add(channel_id)

    def close_channel(self, channel_id):
        self._enabled_channels.remove(channel_id)

    def add_command(self, method: callable, *aliases: str):
        for alias in aliases:
            self._commands[alias] = method

    async def on_message(self, message: typing.Dict):
        assert message['c'] == 'cmd'
        if message['n'] not in self._enabled_channels:
            LOGGER.core.error('Error, message received on closed channel: %s', message)
            return

        try:
            data = message['d'].strip().split(' ')
            if not data:
                raise TypeError('Empty command?')

            entity = Entity(message['e_id'], itsme=True)
            entity.set_component(SystemComponent(connection=message['n']))

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
