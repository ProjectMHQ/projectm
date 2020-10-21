import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.domain.entity import Entity


class InventoryMessages:
    def __init__(self):
        pass

    def target_not_found(self):
        return 'Non lo vedi'

    def target_not_in_room(self):
        return 'Non lo vedi qui'

    def on_drop_item(self, item: Entity):
        return 'Posi {}'.format(item.get_component(AttributesComponent).keyword)

    def on_entity_drop_item(self, item: Entity):
        return '{origin} posa a terra %s' % item.get_component(AttributesComponent).keyword

    def items_to_message(self, items: typing.List[Entity]) -> typing.Dict:
        return {
            "entities": [
                {
                    "entity_id": item.entity_id,
                    "name": item.get_component(AttributesComponent).keyword
                } for item in items
            ]
        }

    def on_drop_multiple_items(self) -> str:
        return "Posi diversi oggetti"

    def on_entity_drops_multiple_items(self) -> str:
        return "{origin} posa diversi oggetti"

    def item_picked(self, item: Entity):
        return 'raccogli {}'.format(item.get_component(AttributesComponent).keyword)

    def entity_picked_item(self, item: Entity):
        return '{origin} raccoglie %s' % item.get_component(AttributesComponent).keyword

    def picked_multiple_items(self) -> str:
        return "Raccogli diversi oggetti"

    def entity_picked_multiple_items(self) -> str:
        return '{origin} raccoglie diversi oggetti'

    def cannot_pick_item(self):
        return 'Non puoi farlo!'
