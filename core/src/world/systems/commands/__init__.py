from core.src.world.actions.disconnect import disconnect_entity
from core.src.world.actions.follow import follow
from core.src.world.actions.go import go_entity

from core.src.world.actions.library import library
from core.src.world.actions.whoami import whoami


def commands_observer_factory(transport):
    from core.src.world.services.transport.socketio_interface import TransportInterface
    from core.src.world.systems.commands.observer import CommandsObserver
    from core.src.world.actions.getmap import getmap
    from core.src.world.actions.look import look
    from core.src.world.actions.move import move_entity

    if isinstance(transport, TransportInterface):
        observer = CommandsObserver(transport)
    else:
        raise NotImplementedError

    observer.add_command(look, 'look')
    observer.add_command(getmap, 'getmap')
    observer.add_command(whoami, 'whoami')
    observer.add_command(move_entity, 'n', 's', 'w', 'e', 'd', 'u')
    observer.add_command(disconnect_entity, 'quit')
    observer.add_command(follow, 'follow')
    observer.add_command(go_entity, 'go')
    observer.add_command(library, '@lib')
    return observer
