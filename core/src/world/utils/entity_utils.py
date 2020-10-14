import typing
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


def get_base_room_for_entity(entity: Entity):
    return PosComponent([19, 1, 0])  # TODO FIXME


def get_index_from_text(text: str) -> typing.Tuple[int, str]:
    if '.' in text:
        _split = text.split('.')
        if len(_split) > 2:
            raise ValueError
        index = int(_split[0]) - 1
        text = _split[1]
    else:
        index = 0
    return index, text


def get_entity_id_from_raw_data_input(
        text: str, totals: int, data: typing.Iterable, index: int = 0
) -> typing.Optional[int]:
    if not data:
        return
    i = 0
    entity_id = None
    for x in range(0, totals):
        for entry in data:
            if entry['data'][x]['keyword'].startswith(text):
                if i == index:
                    entity_id = entry['entity_id']
                    break
                i += 1
    return entity_id


def get_entity_data_from_raw_data_input(
        text: str, totals: int, data: typing.Iterable, index: int = 0
) -> typing.Optional[typing.Dict]:
    if not data:
        return
    i = 0
    for x in range(0, totals):
        for entry in data:
            if entry['data'][x].startswith(text):
                if i == index:
                    return entry
                i += 1


if __name__ == '__main__':
    room_data = [
        {'entity_id': 3, 'data': ['nome1']},
        {'entity_id': 4, 'data': ['nome2']},
        {'entity_id': 6, 'data': ['nome3']},
        {'entity_id': 213, 'data': ['nome4']},
        {'entity_id': 1235, 'data': ['nome5']},
        {'entity_id': 12, 'data': ['']}
    ]
    equipment_data = [
        {'entity_id': 3664, 'data': ['nomaz1']},
        {'entity_id': 345,  'data': ['']},
        {'entity_id': 2136, 'data': ['']},
        {'entity_id': 3337, 'data': ['']}
    ]
    inventory_data = [
        {'entity_id': 3623, 'data': ['']},
    ]

    for ___x in range(0, 20100):
        room_data.append({'entity_id': 10 + ___x, 'data': ['nome{}'.format(100 + ___x)]})

    DATA = [*equipment_data, *inventory_data, *room_data]

    import time
    s = time.time()
    key_to_search = '11111.nom'
    print('Key to search:', key_to_search)
    print('Entries to search:', len(DATA) * len(DATA[0]['data']))
    print('Entity id:', get_entity_id_from_raw_data_input(key_to_search, DATA))
    e = time.time()
    print('Execution time: {:.10f}'.format(e-s))
