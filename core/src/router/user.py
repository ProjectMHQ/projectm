import json

import flask
from flask import request
from flask.views import MethodView

from core.src.utils import ensure_not_logged_in, ensure_logged_in, handle_exception
from core.src.builder import auth_service, user_repository, psql_character_repository
from core.src.database import db_close

bp = flask.Blueprint('profile', __name__)


@handle_exception
@ensure_logged_in
def get_details():
    user = user_repository.get_user_by_field('user_id', request.user['user_id'])
    return flask.jsonify({"data": user.as_dict()})


class CharacterView(MethodView):
    @handle_exception
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

    @handle_exception
    @ensure_logged_in
    def post(self):
        payload = json.loads(request.data.decode())
        user = user_repository.get_user_by_field('user_id', request.user['user_id'])
        character = psql_character_repository.create_character(user, payload['name'])
        return flask.jsonify({"data": character.as_dict()})


bp.add_url_rule(
    '/', view_func=get_details, methods=['GET']
)
bp.add_url_rule(
    '/character', view_func=CharacterView.as_view('CharactersGet'), methods=['GET'], defaults={'character_id': None}
)
bp.add_url_rule(
    '/character', view_func=CharacterView.as_view('CharacterCreate'), methods=['POST'],
)
