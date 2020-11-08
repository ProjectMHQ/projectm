from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.position import PositionComponent
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room


def serialize_system_message_item(item, entity):
    """
    Todo - Implement a better player POV based on memory and other skills.
    """
    if isinstance(item, Room):
        return item.item_type, item.serialize()
    elif isinstance(item, Entity):
        p = item.get_component(PositionComponent)
        if p.coords:
            location = -1
        elif p.parent_of:
            location = p.parent_of
        else:
            location = None
        attributes = item.get_component(AttributesComponent)
        return "entity", {
            "attributes": {
                "name": attributes.name.value,
                "keyword": attributes.keyword.value,
                "description": attributes.description.value
            },
            "location": location
        }
    elif isinstance(item, dict):
        return item
    else:
        raise ValueError(item)
