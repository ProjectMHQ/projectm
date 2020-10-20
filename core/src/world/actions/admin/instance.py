from core.src.world.components.character import CharacterComponent
from core.src.world.components.instance_by import InstanceByComponent
from core.src.world.components.instance_of import InstanceOfComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity


async def instance(entity: Entity, command: str, parent_alias: str, *args):
    if command == 'create':
        instanced = await _create_instance(entity, parent_alias, *args)
        await entity.emit_msg('Entity type {} instanced - Entity ID: {}'.format(parent_alias, instanced.entity_id))
    elif command == 'destroy':
        assert args[0], args
        entity_id_to_delete = int(args[0])
        res = await _destroy_instance(entity, parent_alias, entity_id_to_delete, force=len(args) > 1 and args[1])
        if res:
            await entity.emit_msg('Entity {} deleted: {}'.format(entity_id_to_delete, res))
        else:
            await entity.emit_msg('Cannot do destroy action')
    elif command == 'cleanup':
        await _cleanup_map_from_instance(entity, parent_alias, args[0])


async def _create_instance(entity: Entity, parent_alias: str, *args):
    from core.src.world.builder import world_repository, library_repository
    instanced = library_repository.get_instance_of(parent_alias)
    if not instanced:
        await entity.emit_msg('Cannot obtain instance of {}'.format(parent_alias))
        return
    instanced.set_for_update(InstanceByComponent(entity.entity_id))
    if args:
        location = args[0]
        if location not in ('.', '@here'):
            await entity.emit_msg('Error, location {} invalid (allowed location: ".")'.format(location))
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        instanced.set_for_update(pos)
    else:
        await entity.emit_msg('Inventory not implemented, please specify a location')
    await world_repository.save_entity(instanced)
    return instanced


async def _destroy_instance(entity: Entity, parent_alias: str, entity_id_to_delete: int, force=False):
    from core.src.world.builder import world_repository
    if not await world_repository.entity_exists(entity_id_to_delete):
        await entity.emit_msg('Entity does not exists, use cleanup (bug)')
        return
    instance_of = await world_repository.get_component_value_by_entity_id(entity_id_to_delete, InstanceOfComponent)
    is_character = await world_repository.get_component_value_by_entity_id(entity_id_to_delete, CharacterComponent)
    if is_character:
        await entity.emit_msg('Cannot destroy characters with this command')
        return
    if force != '--force':
        if instance_of and (parent_alias != instance_of.value):
            await entity.emit_msg('Entity {} is not type <{}>, it\'s <{}> instead'.format(
                entity_id_to_delete, parent_alias, instance_of.value
            ))
            return
    res = await world_repository.delete_entity(entity_id_to_delete)
    return res


async def _cleanup_map_from_instance(entity: Entity, entity_id, position):
    from core.src.world.builder import world_repository, map_repository
    entity_id = int(entity_id)
    if await world_repository.entity_exists(entity_id):
        await entity.emit_msg('Entity exists, destroy it first'.format(entity_id))
        return
    if ',' in position:
        pos = PosComponent([int(x) for x in position.split(',')])
    elif '@here' == position:
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    else:
        await entity.emit_msg('Invalid argument {}'.format(position))
        return
    entity_id_position = await world_repository.get_component_value_by_entity_id(entity_id, PosComponent)
    if entity_id_position and entity_id_position.value != pos.value:
        await entity.emit_msg('Entity {} is at another position: {}'.format(entity_id, entity_id_position.value))
    removed = bool(await map_repository.remove_entity_from_map(entity_id, pos))
    await entity.emit_msg('Entity {} {} removed from position {}'.format(entity_id, '' if removed else 'not', pos))
