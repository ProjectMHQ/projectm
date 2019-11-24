import typing
from etc import settings
from core.src.world.entity import Entity, EntityID
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
        from core.src.world.run_worker import singleton_actions_scheduler
        await singleton_actions_scheduler.stop_current_action_if_exists(message['e_id'])
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
        except KeyError:
            if settings.RUNNING_TESTS:
                raise
            await self._on_error(message, "Command not found: %s" % data[0])
        except TypeError as exc:
            if settings.RUNNING_TESTS:
                raise
            await self._on_error(message, "Command error: %s" % str(exc))

    def _on_error(self, message, error):
        return self.transport.send(namespace=message['n'], payload={"event": "cmd", "error": error})
