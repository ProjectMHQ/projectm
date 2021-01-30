from core.src.world.components.position import PositionComponent
from core.src.world.components.system import SystemComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import load_components
from core.src.world.utils.messaging import emit_msg


async def instance(entity: Entity, command: str, parent_alias: str, *args):
    if command == 'create':
        instanced = await _create_instance(entity, parent_alias, *args)
        if instanced:
            await emit_msg(entity, 'Entity type {} instanced - Entity ID: {}'.format(parent_alias, instanced.entity_id))
        else:
            await emit_msg(entity, 'Instance failed')
    elif command == 'destroy':
        assert args[0], args
        entity_id_to_delete = int(args[0])
        res = await _destroy_instance(entity, parent_alias, entity_id_to_delete, force=len(args) > 1 and args[1])
        if res:
            await emit_msg(entity, 'Entity {} deleted: {}'.format(entity_id_to_delete, res))
        else:
            await emit_msg(entity, 'Cannot do destroy action')
    else:
        await emit_msg(entity, 'error, use @inst [create|destroy] libname loc')


async def _create_instance(entity: Entity, parent_alias: str, *args):
    from core.src.world.builder import world_repository, library_repository
    instanced = library_repository.get_instance_of(parent_alias, entity)
    if not instanced:
        await emit_msg(entity, 'Cannot obtain instance of {}'.format(parent_alias))
        return
    if args:
        location = args[0]
        if location not in ('.', '@here'):
            await emit_msg(entity, 'Error, location {} invalid (allowed location: ".")'.format(location))
        await load_components(entity, PositionComponent)
        instanced.set_for_update(entity.get_component(PositionComponent))
    else:
        await emit_msg(entity, 'Inventory not implemented, please specify a location')
    await world_repository.save_entity(instanced)
    return instanced


async def _destroy_instance(entity: Entity, parent_alias: str, entity_id_to_delete: int, force=False):
    from core.src.world.builder import world_repository
    if not await world_repository.entity_exists(entity_id_to_delete):
        await emit_msg(entity, 'Entity does not exists, use cleanup (bug)')
        return
    entity_to_delete = Entity(entity_id_to_delete)
    await load_components(entity_to_delete, (SystemComponent, 'instance_of', 'character'))
    system_component = entity_to_delete.get_component(SystemComponent)
    if system_component.character:
        await emit_msg(entity, 'Cannot destroy characters with this command')
        return
    if force != '--force':
        if system_component.instance_of and (parent_alias != system_component.instance_of):
            await emit_msg(
                entity,
                    'Entity {} is not type <{}>, it\'s <{}> instead'.format(
                    entity_id_to_delete, parent_alias, system_component.instance_of
                )
            )
            return
    res = await world_repository.delete_entity(entity_id_to_delete)
    return res
