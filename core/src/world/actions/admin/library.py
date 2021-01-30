from core.src.world.domain.entity import Entity
from core.src.world.systems.library.service import LibrarySystemService
from core.src.world.utils.messaging import emit_msg


async def library(entity: Entity, *args):
    system = LibrarySystemService(entity)
    if not args:
        await emit_msg(entity, 'Missing argument.')
        return
    action = args[0]
    if action == 'load':
        await system.load('json', args[1])
    elif action == 'reload':
        await system.load('json', args[1], overwrite=True)
    elif action == 'ls':
        await system.ls(len(args) > 1 and args[1] or '*')
    else:
        await emit_msg(entity, 'action {} not recognized'.format(action))
