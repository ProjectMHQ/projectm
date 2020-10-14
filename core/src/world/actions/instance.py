from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


async def instance(entity: Entity, parent_alias: str, *args):
    from core.src.world.builder import world_repository, library_repository
    instanced = library_repository.get_instance_of(parent_alias)
    if not instanced:
        await entity.emit_msg('Cannot obtain instance of {}'.format(parent_alias))
        return
    if args:
        location = args[0]
        if location != '.':
            await entity.emit_msg('Error, location {} invalid (allowed location: ".")'.format(location))
    else:
        await entity.emit_msg('Inventory not implemented, please specify a location')
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    instanced.set(pos)
    await world_repository.save_entity(instanced)
    await entity.emit_msg('Entity type {} instanced - Entity ID: {}'.format(parent_alias, instanced.entity_id))
