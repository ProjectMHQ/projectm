import typing


class MessagesObserver:
    def __init__(self, transport):
        self._commands = {}
        self.transport = transport

    def add_command(self, command: str, method: callable):
        self._commands[command] = method

    async def on_message(self, message: typing.Dict):
        assert message['c'] == 'cmd'
        data = message['d'].strip().split(' ')
        try:
            self._commands[message](
                *data,
                callback=lambda res: self._bake_callback(message, res),
                errback=lambda err: self._bake_errback(message, err)
            )

        except KeyError:
            await self._on_error(
                message, "Command not found: %s" % data[0]
            )
        except TypeError as exc:
            await self._on_error(
                message, "Command error: %s" % str(exc)
            )

    def _bake_callback(self, message, response):
        self.transport.emit(message['n'], {"cmd": message["c":], "response": response})

    def _bake_errback(self, message, error):
        self.transport.emit(message['n'], {"cmd": message["c":], "error": error})

    def _on_error(self, message, error):
        self.transport.emit(message['n'], {"cmd": message["c":], "error": error})
