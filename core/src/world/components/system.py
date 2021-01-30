from core.src.world.components.base import ComponentTypeEnum
from core.src.world.components.base.structcomponent import StructComponent


class SystemComponent(StructComponent):
    enum = ComponentTypeEnum.SYSTEM
    libname = "system"

    meta = (
        ("user_id", str),
        ("connection", str),
        ("created_at", int),
        ("receive_events", bool),
        ("instance_by", int),
        ("instance_of", str)
    )
    indexes = (
        ("connection", bool),
        ("user_id", str),
        ("instance_of", str)
    )
