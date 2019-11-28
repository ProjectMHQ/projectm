class PubSubObserver:
    def __init__(self, entity):
        self._commands = {}
        self._entity = entity

    async def on_event(self, message, room):
        print('on_event in room', room, 'message', message)
