from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.parent_of import ParentOfComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room


def serialize_system_message_item(item, entity):
    """
    Todo - Implement a better player POV based on memory and other skills.
    """
    if isinstance(item, Room):
        return item.item_type, item.serialize()
    elif isinstance(item, Entity):
        if item.get_component(PosComponent):
            location = -1
        elif item.get_component(ParentOfComponent).parent_id == entity.entity_id:
            location = item.get_component(ParentOfComponent).location
        else:
            location = None
        attributes = item.get_component(AttributesComponent)
        return "entity", {
            "attributes": {
                "name": attributes.name,
                "keyword": attributes.keyword,
                "description": attributes.description
            },
            "location": location
        }
    elif isinstance(item, dict):
        return item
    else:
        raise ValueError(item)
