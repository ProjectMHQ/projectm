from core.src.world.components.attributes import AttributesComponent
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room


def serialize_system_message_item(item):
    """
    Todo - Implement a better player POV based on memory and other skills.
    """
    if isinstance(item, Room):
        return item.item_type, item.serialize()
    elif isinstance(item, Entity):
        return "entity", {
            "attributes": item.get_component(AttributesComponent).value,
        }
    elif isinstance(item, dict):
        return item
    else:
        raise ValueError
