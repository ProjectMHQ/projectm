import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.character import CharacterComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.instance_of import InstanceOfComponent
from core.src.world.components.pos import PosComponent


BaseComponents = typing.NamedTuple(
    "BaseComponents", (
        ("instance_of", InstanceOfComponent),
        ("attributes", AttributesComponent),
        ("pos", PosComponent),
        ("connection", ConnectionComponent),
        ("character", CharacterComponent)
    )
)

ActionTarget = typing.NamedTuple(
    "ActionTarget", (
        ("components", BaseComponents),
    )
)


async def get_base_components_for_entity_id(entity_id: int) -> BaseComponents:
    from core.src.world.builder import world_repository
    response = await world_repository.get_base_components_for_entity_id(entity_id)
    return BaseComponents(
        instance_of=response['instance_of'],
        attributes=response['attributes'],
        pos=response['position'],
        connection=response['connection'],
        character=response['is_character']
    )


async def get_action_target(search_response, ensure_available=True) -> typing.Optional[ActionTarget]:
    from core.src.world.utils.world_types import Transport
    from core.src.world.domain.entity import Entity
    target = Entity(search_response.entity_id)
    target_components = await get_base_components_for_entity_id(search_response.entity_id)
    if ensure_available and\
            (target_components.pos.value != search_response.room.position.value) or \
            (not target_components.connection):
        return
    from core.src.world.builder import transport
    target.transport = Transport(namespace=target_components.connection.value, transport=transport)
    return ActionTarget(
        components=target_components,
    )
