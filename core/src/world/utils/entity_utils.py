from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


def get_base_room_for_entity(entity: Entity):
    return PosComponent([1, 1, 0])  # TODO FIXME
