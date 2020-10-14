from core.src.world.components.instance_by import InstanceByComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity


async def instance(entity: Entity, command: str, parent_alias: str, *args):
    if command == 'create':
        instanced = await _create_instance(entity, parent_alias, *args)
        await entity.emit_msg('Entity type {} instanced - Entity ID: {}'.format(parent_alias, instanced.entity_id))


async def _create_instance(entity: Entity, parent_alias: str, *args):
    from core.src.world.builder import world_repository, library_repository
    instanced = library_repository.get_instance_of(parent_alias)
    if not instanced:
        await entity.emit_msg('Cannot obtain instance of {}'.format(parent_alias))
        return
    instanced.set(InstanceByComponent(entity.entity_id))
    if args:
        location = args[0]
        if location not in ('.', '@here'):
            await entity.emit_msg('Error, location {} invalid (allowed location: ".")'.format(location))
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        instanced.set(pos)
    else:
        await entity.emit_msg('Inventory not implemented, please specify a location')
    await world_repository.save_entity(instanced)
    return instanced


async def _destroy_instance(entity: Entity, parent_alias: str, *args):
    pass
