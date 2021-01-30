from core.src.world.utils.world_types import DirectionEnum


class MovementMessages:
    def __init__(self):
        self.opposite_direction = {
            DirectionEnum.NORTH: DirectionEnum.SOUTH,
            DirectionEnum.SOUTH: DirectionEnum.NORTH,
            DirectionEnum.EAST: DirectionEnum.WEST,
            DirectionEnum.WEST: DirectionEnum.EAST,
            DirectionEnum.UP: DirectionEnum.DOWN,
            DirectionEnum.DOWN: DirectionEnum.UP
        }
        self._direction = {
            DirectionEnum.NORTH: 'nord',
            DirectionEnum.SOUTH: 'sud',
            DirectionEnum.EAST: 'est',
            DirectionEnum.WEST: 'ovest',
            DirectionEnum.UP: 'l\'alto',
            DirectionEnum.DOWN: 'il basso'
        }

    def invalid_direction(self):
        return 'Non puoi andare in quella direzione!'

    def not_recognized_direction(self):
        return 'Non è una direzione valida'

    def movement_begins(self, direction):
        return 'inizi a muoverti verso {}'.format(self._direction[direction])

    def movement_success(self, direction):
        return 'vai a {}'.format(self._direction[direction])

    def entity_movement_begin_template(self, direction):
        return '{origin} inizia a muoversi verso %s' % self._direction[direction]

    def entity_movement_success_template(self, direction):
        return '{origin} va verso %s' % self._direction[direction]

    def entity_movement_success_arrive_template(self, direction):
        return '{origin} arriva da %s' % self._direction[self.opposite_direction[direction]]
