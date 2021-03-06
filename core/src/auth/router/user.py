import flask
from flask import request
from flask.views import MethodView

from core.src.auth.utils import ensure_logged_in
from core.src.auth.builder import user_repository

bp = flask.Blueprint('profile', __name__)


@ensure_logged_in
def get_details():
    user = user_repository.get_user_by_field('user_id', request.user['user_id'])
    return flask.jsonify({"data": user.as_dict()})


class CharacterView(MethodView):
    @ensure_logged_in
    def get(self, character_id):
        user = user_repository.get_user_by_field('user_id', request.user['user_id'])
        if not character_id:
            characters = user.get_characters()
            data = [c.as_dict() for c in characters]
        else:
            character = user.get_character(character_id)
            data = character.as_dict()
        return flask.jsonify({"data": data})


bp.add_url_rule(
    '/', view_func=get_details, methods=['GET']
)
bp.add_url_rule(
    '/character', view_func=CharacterView.as_view('CharactersGet'), methods=['GET'], defaults={'character_id': None}
)
