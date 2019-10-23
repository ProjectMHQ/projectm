import json

import flask
from flask import request

from core.src.authentication.scope import ensure_not_logged_in, ensure_logged_in
from core.src.builder import user_service, user_repository, character_repository
from core.src.database import db_close
from core.src.utils.tools import handle_exception

bp = flask.Blueprint('profile', __name__)


@db_close
@handle_exception
@ensure_logged_in
def get_details():
    user = user_repository.get_user_by_field('user_id', request.user['user_id'])
    return flask.jsonify(
        {
            "data": user.as_dict()
        }
    )


@db_close
@handle_exception
@ensure_logged_in
def get_characters():
    user = user_repository.get_user_by_field(
        'user_id', request.user['user_id']
    )
    characters = user.get_characters()
    return flask.jsonify(
        {
            "data": [c.as_dict() for c in characters]
        }
    )


bp.add_url_rule(
    '/', view_func=get_details, methods=['GET']
)
bp.add_url_rule(
    '/characters', view_func=get_characters, methods=['GET']
)

