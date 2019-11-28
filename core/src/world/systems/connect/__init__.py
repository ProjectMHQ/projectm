from core.src.world.actions.look import look
from core.src.world.services.websocket.socketio_interface import TransportInterface
from core.src.world.systems.commands.observer import CommandsObserver


def commands_observer_factory(transport):
    if isinstance(transport, TransportInterface):
        observer = CommandsObserver(transport)
    else:
        raise NotImplementedError

    observer.add_command('look', look)
    return observer
