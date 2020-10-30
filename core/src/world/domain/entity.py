import typing

from core.src.world.components.base import ComponentType
from core.src.world.components.base.structcomponent import StructComponent
from core.src.world.domain import DomainObject


class Entity(DomainObject):
    item_type = "entity"

    def __init__(self, entity_id: typing.Optional[int] = None, itsme=False):
        self._entity_id = entity_id
        self._pending_changes = {}
        self._bounds = []
        self._components = {}
        self._room = None
        self.itsme = itsme

    def set_room(self, room):
        self._room = room
        return self

    def get_room(self):
        return self._room

    def get_view_size(self):
        return 15

    def set_for_update(self, component: ComponentType):
        self._pending_changes[component.enum] = component
        if isinstance(component, StructComponent) and component.bounds:
            if component not in self._bounds:
                self._bounds.append(component)
        return self

    @property
    def entity_id(self) -> int:
        return self._entity_id

    @entity_id.setter
    def entity_id(self, value: int):
        assert not self._entity_id
        self._entity_id = value

    @property
    def pending_changes(self):
        return self._pending_changes

    def bounds(self):
        return self._bounds

    def clear_bounds(self):
        self._bounds = []
        return self

    def add_bound(self, component):
        self._bounds.append(component)
        return self

    def set_component(self, component: ComponentType):
        self._components[component.enum] = component
        if getattr(component, 'bounds', None):
            self.add_bound(component)
        return self

    def get_component(self, component: typing.Type[ComponentType]):
        component = self._components.get(component.enum)
        component and component.set_owner(self)
        return component
