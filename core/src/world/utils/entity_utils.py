import typing
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


def get_base_room_for_entity(entity: Entity):
    return PosComponent([19, 1, 0])  # TODO FIXME


def data_inventory_to_string(data: typing.List) -> typing.Tuple[str, int]:
    tot = 0
    basestr = "|"
    aggs_len = []
    for z in data:
        if z.get('name'):
            basestr += '{}:{}|'.format(z['name'], z['e_id'])
            tot += 1
        aggs_len.append(len(z['aggs']))
    for _x in range(0, max(aggs_len)):
        for i, y in enumerate(data):
            if _x < aggs_len[i]:
                basestr += '{}:{}|'.format(y['aggs'][_x], y['e_id'])
                tot += 1
    return basestr, tot


def get_entity_id_from_string_inventory(text, data) -> typing.Optional[int]:
    if not data:
        return
    if '.' in text:
        _split = text.split('.')
        if len(_split) > 2:
            raise ValueError
        index = int(_split[0]) - 1
        text = _split[1]
    else:
        index = 0
    p = 0
    for _ in range(0, index+1):
        _p = data.find(text, p if not p else (p + 1))
        if _p == p or _p <= 0:
            return
        p = _p
    return int(data[p:data.find('|', p)].split(':')[1])


if __name__ == '__main__':
    room_data = [
        {'e_id': 3, 'name': 'pippo', 'aggs': ['biondo', 'medio', 'elfo', 'sinoriano']},
        {'e_id': 6, 'name': 'pluto', 'aggs': ['biondo', 'medio', 'elfo', 'alwenion']},
        {'e_id': 213, 'name': 'paperino', 'aggs': ['calvo', 'alto', 'umano']},
        {'e_id': 1235, 'name': 'paperina', 'aggs': ['guardia elfica']},
        {'e_id': 12, 'name': '', 'aggs': ['umano']}
    ]
    equipment_data = [
        {'e_id': 3664, 'name': '', 'aggs': ['jacket', 'cotton', 'green']},
        {'e_id': 345, 'name': '', 'aggs': ['vest', 'cotton', 'black']},
        {'e_id': 2136, 'name': '', 'aggs': ['pants', 'cotton', 'black']},
        {'e_id': 3337, 'name': '', 'aggs': ['shoes', 'leather', 'black', 'weird', 'elven']}
    ]
    inventory_data = [
        {'e_id': 3623, 'name': '', 'aggs': ['sword', 'steel', 'long', 'big', 'uncut', 'green', 'painted', 'whatever']},
    ]

    for ___x in range(0, 1000):
        room_data.append({'e_id': 10 + ___x, 'name': '', 'aggs': ['sword', 'steel', 'long', 'big', 'uncut']})

    DATA = [*equipment_data, *inventory_data, *room_data]

    import time
    s = time.time()
    _data, t = data_inventory_to_string(DATA)
    key_to_search = '1000.swo'
    print('Key to search:', key_to_search)
    print('Entries to search:', t)
    print('Entity id:', get_entity_id_from_string_inventory(key_to_search, _data))
    e = time.time()
    print('Execution time: {:.10f}'.format(e-s))
