from core.src.world.actions.inventory.inventory_messages import InventoryMessages
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.position import PositionComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import load_components, search_entities_in_container_by_keyword
from core.src.world.utils.messaging import emit_sys_msg

messages = InventoryMessages()


async def inventory(entity: Entity):
    await load_components(entity, PositionComponent, InventoryComponent)
    inventory = entity.get_component(InventoryComponent)
    items = await search_entities_in_container_by_keyword(inventory, '*')
    await emit_sys_msg(entity, 'inventory', messages.items_to_message(items))
