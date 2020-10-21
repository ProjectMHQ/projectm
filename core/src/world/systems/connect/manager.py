import typing


class ConnectionsManager:
    def __init__(self):
        self._transports_by_entity: typing.Dict[int, int] = {}
        self._transports_by_transport: typing.Dict[int, int] = {}

    def set_transport(self, entity_id: int, transport_id):
        self._transports_by_entity[entity_id] = transport_id
        self._transports_by_transport[transport_id] = entity_id

    def remove_transport(self, entity_id: int):
        transport_id = self._transports_by_entity.get(entity_id)
        self._transports_by_entity.pop(entity_id, None)
        self._transports_by_transport.pop(transport_id, None)

    def get_transport_by_entity_id(self, entity_id: int):
        return self._transports_by_entity.get(entity_id)
