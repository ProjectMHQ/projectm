from core.src.world.components import ComponentType
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.character import CharacterComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.created_at import CreatedAtComponent
from core.src.world.components.instance_of import InstanceOfComponent
from core.src.world.components.pos import PosComponent
from core.src.world.components.weapon import WeaponComponent


def get_component_by_type(component_type_string) -> ComponentType:
    return {
        'attributes': AttributesComponent,
        'character': CharacterComponent,
        'connection': ConnectionComponent,
        'created_at': CreatedAtComponent,
        'instance_of': InstanceOfComponent,
        'pos': PosComponent,
        'weapon': WeaponComponent,
    }[component_type_string]
