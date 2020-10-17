from core.src.world.utils.utils import ActionTarget
from core.src.world.domain.room import Room


def serialize_system_message_item(item):
    """
    Todo - Implement a better player POV based on memory and other skills.
    """
    if isinstance(item, Room):
        return item.item_type, item.serialize()
    elif isinstance(item, ActionTarget):
        return "entity", {
            "attributes": item.components.attributes.value,
        }
