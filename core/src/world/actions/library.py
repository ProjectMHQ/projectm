from core.src.world.entity import Entity
from core.src.world.systems.library.service import LibrarySystemService


async def library(entity: Entity, action: str, *args):
    system = LibrarySystemService(entity)
    if not args:
        await entity.emit_msg('Missing argument.')
        return
    if action == 'load':
        await system.load('json', args[0])
    if action == 'reload':
        await system.load('json', args[0], overwrite=True)
    elif action == 'ls':
        await system.ls(args and args[0] or '*')
    else:
        await entity.emit_msg('action {} not recognized'.format(action))
