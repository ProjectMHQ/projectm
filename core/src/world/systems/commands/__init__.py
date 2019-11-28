def commands_observer_factory(transport):
    from core.src.world.services.websocket.socketio_interface import TransportInterface
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
    observer.add_command(move_entity, 'n', 's', 'w', 'e', 'd', 'u')
    return observer
