import typing

from core.src.websocket.utilities import ws_commands_extractor


class WebsocketWorldCommandsInterface:
    def __init__(self, ctx):
        self._ctx = ctx
        self._commands = {}
        self._errors_handlers = set()

    @property
    def ctx(self):
        return self._ctx

    def add_command(self, command: str, method: callable, aliases=[]):
        self._commands[command] = method
        for alias in aliases:
            self._commands[alias] = method

    def on_command(self, data: str, topic: str):
        command, arguments = ws_commands_extractor(data)
        cmd = self._commands.get(command)
        if not cmd:
            self.on_error(command)
            return
        cmd(*arguments)

    def on_error(self, command: str):
        for handler in self._errors_handlers:
            handler(command)
