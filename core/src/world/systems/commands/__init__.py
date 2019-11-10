from core.src.world.actions import look
from core.src.world.systems.commands.workers_messages_observer import MessagesObserver


def commands_observer_factory(transport):
    from socketio import AsyncRedisManager
    if isinstance(transport, AsyncRedisManager):
        observer = MessagesObserver(transport)
    else:
        raise NotImplementedError

    observer.add_command('look', look)
    return observer
