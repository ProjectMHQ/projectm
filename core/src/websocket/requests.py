import typing

from click import exceptions


class RequestsProcessorInterface:
    def __init__(self):
        self._commands = {}

    def add_command(self, command: str, method: callable):
        self._commands[command] = method

    def on_command(self, command: str, arguments: typing.List[str], callback=None):
        cmd = self._commands.get(command)
        if not cmd:
            raise exceptions.MissingCommandException
        res = cmd(command, arguments)
        callback and callback(res)
