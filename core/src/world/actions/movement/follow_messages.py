class FollowMessages:
    def target_not_found(self):
        return 'Non lo vedi qui!'

    def already_following_that_target(self):
        return 'Lo stai già seguendo'

    def follow_is_loop(self):
        return 'Non puoi seguirlo'

    def follow_entity(self, name: str):
        return 'Segui {}'.format(name)

    def entity_follows_entity_template(self):
        return '{origin} segue {target}'

    def not_following_anyone(self):
        return 'Non stai seguendo nessuno'

    def do_unfollow(self, name: str):
        return 'Smetti di seguire {}'.format(name)

    def entity_stop_following_you(self, name: str):
        return '{} smette di seguirti'.format(name)

    def entity_is_following_you(self, name: str):
        return '{} inizia a seguirti'.format(name)
