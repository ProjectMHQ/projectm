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
            if not data:
                raise TypeError('Empty command?')

            await self._commands[data[0]](
                message['e_id'],
                *data[1:],
                callback=lambda res: self._bake_callback(message, res),
                errback=lambda err: self._on_error(message, err)
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
        return self.transport.emit(message['n'], message['c'], response)

    def _on_error(self, message, error):
        return self.transport.emit(message['n'], message['c'], error)
