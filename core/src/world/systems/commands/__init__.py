from core.src.world.actions.inventory.put import put
from core.src.world.actions.system.disconnect import disconnect_entity
from core.src.world.actions.inventory.drop import drop
from core.src.world.actions.movement.follow import follow
from core.src.world.actions.movement.go import go_entity
from core.src.world.actions.admin.instance import instance
from core.src.world.actions.admin.library import library
from core.src.world.actions.inventory.pick import pick
from core.src.world.actions.system.whoami import whoami
from core.src.world.actions.system.getmap import getmap
from core.src.world.actions.look.look import look
from core.src.world.actions.movement.move import move_entity


def commands_observer_factory(transport):
    from core.src.world.systems.commands.observer import CommandsObserver

    from core.src.world.transport.socketio_interface import TransportInterface
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
    observer.add_command(pick, 'pick')
    observer.add_command(drop, 'drop')
    observer.add_command(put, 'put')

    observer.add_command(library, '@lib')
    observer.add_command(instance, '@inst')
    return observer
