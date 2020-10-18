class FollowMessages():
    def target_not_found(self):
        return 'target not found'

    def already_following_target(self):
        return 'already following target'

    def follow_is_loop(self):
        return 'follow is loop'

    def follow_entity(self, name: str):
        return 'following {}'.format(name)

    def entity_follows_entity_template(self):
        return '{origin} follows {target}'

    def not_following_anyone(self):
        return 'not following anyone'

    def do_unfollow(self, name: str):
        return 'stop following {}'.format(name)
