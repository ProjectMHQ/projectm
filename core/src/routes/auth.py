import json

import flask
from flask import request

from core.src.authentication.scope import ensure_not_logged_in, ensure_logged_in
from core.src.builder import auth_service, character_repository
from core.src.database import db_close
from core.src.utils.tools import handle_exception

bp = flask.Blueprint('auth', __name__)


@db_close
@handle_exception
@ensure_not_logged_in
def handle_email_address_confirmation(email_token):
    auth_service.confirm_email_address(email_token)
    return flask.Response(response='EMAIL_CONFIRMED')


@db_close
@handle_exception
@ensure_not_logged_in
def handle_signup():
    payload = json.loads(request.data)
    auth_service.signup(payload.get('email'), payload.get('password'))
    return flask.Response(response='SIGNUP_CONFIRMED')


@db_close
@handle_exception
@ensure_not_logged_in
def handle_login():
    payload = json.loads(request.data)
    login_response = auth_service.login(payload.get('email'), payload.get('password'))
    response = flask.jsonify({"user_id": login_response['user_id']})
    response.set_cookie('Authorization', 'Bearer {}'.format(login_response['token']))
    return response


@db_close
@handle_exception
@ensure_logged_in
def handle_logout():
    auth_service.logout()
    response = flask.Response(response='LOGOUT_CONFIRMED')
    response.set_cookie('Authorization', '')
    return response


@db_close
@handle_exception
@ensure_logged_in
def handle_new_token():
    payload = json.loads(request.data)
    if payload['entity_type'] == 'character':
        character = character_repository.get_character_by_field(
            'character_id', payload['entity_id'], user_id=request.user['user_id']
        )
        character.ensure_can_authenticate()
        auth_response = auth_service.authenticate_character(character.as_dict(context='token'))
        response = flask.jsonify({"character_id": auth_response['character_id']})
        response.set_cookie('WS-Authorization', 'Bearer {}'.format(auth_response['token']))
        return response

    return flask.Response(response='WRONG_ENTITY_TYPE', status=401)


bp.add_url_rule(
    '/confirm_email/<string:email_token>', view_func=handle_email_address_confirmation, methods=['GET']
)
bp.add_url_rule(
    '/signup', view_func=handle_signup, methods=['POST']
)
bp.add_url_rule(
    '/login', view_func=handle_login, methods=['POST']
)
bp.add_url_rule(
    '/logout', view_func=handle_logout, methods=['POST']
)
bp.add_url_rule(
    '/token', view_func=handle_new_token, methods=['POST']
)
