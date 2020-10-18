class MovementMessages:
    def invalid_direction(self):
        return 'Non puoi andare in quella direzione!'

    def not_recognized_direction(self):
        return 'Non è una direzione valida'

    def movement_begins(self, direction):
        return 'inizi a muoversi versi {}'.format(direction)

    def entity_begin_movement_template(self, direction):
        return '{origin} inizia a muoversi verso %s' % direction

    def movement_success(self, direction):
        return 'vai a {}'.format(direction)
