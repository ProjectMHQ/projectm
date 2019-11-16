from core.src.world.actions.look import look
from core.src.world.services.socketio_interface import TransportInterface
from core.src.world.systems.commands.workers_messages_observer import MessagesObserver


def commands_observer_factory(transport):
    if isinstance(transport, TransportInterface):
        observer = MessagesObserver(transport)
    else:
        raise NotImplementedError

    observer.add_command('look', look)
    return observer
