import typing


class WebsocketRequestsProcessorInterface:
    def __init__(self):
        self._commands = {}
        self._errors_handlers = set()

    def add_command(self, command: str, method: callable):
        self._commands[command] = method

    def on_command(self, command: str, arguments: typing.List[str], callback=None):
        cmd = self._commands.get(command)
        if not cmd:
            self.on_error(command)
            return
        res = cmd(*arguments)
        callback and callback(res)

    def on_error(self, command: str):
        for handler in self._errors_handlers:
            handler(command)
