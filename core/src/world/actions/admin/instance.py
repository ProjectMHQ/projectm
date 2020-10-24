from core.src.world.components.character import CharacterComponent
from core.src.world.components.instance_of import InstanceOfComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
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
    elif command == 'cleanup':
        await _cleanup_map_from_instance(entity, parent_alias, args[0])


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
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        instanced.set_for_update(pos)
    else:
        await emit_msg(entity, 'Inventory not implemented, please specify a location')
    await world_repository.save_entity(instanced)
    return instanced


async def _destroy_instance(entity: Entity, parent_alias: str, entity_id_to_delete: int, force=False):
    from core.src.world.builder import world_repository
    if not await world_repository.entity_exists(entity_id_to_delete):
        await emit_msg(entity, 'Entity does not exists, use cleanup (bug)')
        return
    instance_of = await world_repository.get_component_value_by_entity_id(entity_id_to_delete, InstanceOfComponent)
    is_character = await world_repository.get_component_value_by_entity_id(entity_id_to_delete, CharacterComponent)
    if is_character:
        await emit_msg(entity, 'Cannot destroy characters with this command')
        return
    if force != '--force':
        if instance_of and (parent_alias != instance_of.value):
            await emit_msg(
                entity,
                    'Entity {} is not type <{}>, it\'s <{}> instead'.format(
                    entity_id_to_delete, parent_alias, instance_of.value
                )
            )
            return
    res = await world_repository.delete_entity(entity_id_to_delete)
    return res


async def _cleanup_map_from_instance(entity: Entity, entity_id, position):
    from core.src.world.builder import world_repository, map_repository
    entity_id = int(entity_id)
    if await world_repository.entity_exists(entity_id):
        await emit_msg(entity, 'Entity exists, destroy it first'.format(entity_id))
        return
    if ',' in position:
        pos = PosComponent([int(x) for x in position.split(',')])
    elif '@here' == position:
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    else:
        await emit_msg(entity, 'Invalid argument {}'.format(position))
        return
    entity_id_position = await world_repository.get_component_value_by_entity_id(entity_id, PosComponent)
    if entity_id_position and entity_id_position.value != pos.value:
        await emit_msg(entity, 'Entity {} is at another position: {}'.format(entity_id, entity_id_position.value))
    removed = bool(await map_repository.remove_entity_from_map(entity_id, pos))
    await emit_msg(entity, 'Entity {} {} removed from position {}'.format(entity_id, '' if removed else 'not', pos))
