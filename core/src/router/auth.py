import json

import flask
from flask import request

from core.src.utils import ensure_not_logged_in, ensure_logged_in
from core.src.builder import auth_service, psql_character_repository
from core.src.logging_factory import LOGGER

bp = flask.Blueprint('auth', __name__)


@ensure_not_logged_in
def handle_email_address_confirmation(email_token):
    LOGGER.core.info('handle_email_address_confirmation: %s', email_token)
    auth_service.confirm_email_address(email_token)
    return flask.Response(response='EMAIL_CONFIRMED')


@ensure_not_logged_in
def handle_signup():
    LOGGER.core.info('handle_signup: %s', request.data)
    payload = json.loads(request.data)
    auth_service.signup(payload.get('email'), payload.get('password'))
    return flask.Response(response='SIGNUP_CONFIRMED')


@ensure_not_logged_in
def handle_login():
    LOGGER.core.info('handle_login: %s', request.data)
    payload = json.loads(request.data)
    login_response = auth_service.login(payload.get('email'), payload.get('password'))
    response = flask.jsonify({"user_id": login_response['user_id']})
    response.set_cookie(
        'Authorization', 'Bearer {}'.format(login_response['token']),
        expires=login_response['expires_at']
    )
    return response


@ensure_logged_in
def handle_logout():
    LOGGER.core.info('handle_logut')
    auth_service.logout()
    response = flask.Response(response='LOGOUT_CONFIRMED')
    response.set_cookie('Authorization', '', expires=0)
    
    return response


@ensure_logged_in
def handle_new_token():
    LOGGER.core.info('handle_new_token: %s', request.data)
    payload = json.loads(request.data)
    if payload['context'] == 'world:create':
        auth_response = auth_service.get_token_for_new_character()
    elif payload['context'] == 'world:auth':
        character = psql_character_repository.get_character_by_field(
            'character_id', payload['id'], user_id=request.user['user_id']
        )
        character.ensure_can_authenticate()
        auth_response = auth_service.get_token_for_existing_character(character.character_id)
    else:
        return flask.Response(response='WRONG_ENTITY_TYPE', status=401)

    response = flask.jsonify(
        {
            "expires_at": auth_response['expires_at'],
            "token": auth_response['token']
        }
    )
    return response


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
