import json

import flask
from flask import request

from core.src.utils import ensure_not_logged_in, ensure_logged_in, handle_exception
from core.src.builder import auth_service, psql_character_repository
from core.src.database import db_close
from core.src.logging_factory import LOGGING_FACTORY

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
    LOGGING_FACTORY.core.info('Signup: %s', payload)
    auth_service.signup(payload.get('email'), payload.get('password'))
    return flask.Response(response='SIGNUP_CONFIRMED')


@db_close
@handle_exception
@ensure_not_logged_in
def handle_login():
    payload = json.loads(request.data)
    LOGGING_FACTORY.core.info('Login: %s', payload)
    login_response = auth_service.login(payload.get('email'), payload.get('password'))
    response = flask.jsonify({"user_id": login_response['user_id']})
    response.set_cookie(
        'Authorization', 'Bearer {}'.format(login_response['token']),
        expires=login_response['expires_at']
    )
    return response


@db_close
@handle_exception
@ensure_logged_in
def handle_logout():
    LOGGING_FACTORY.core.info('Logout')  
    auth_service.logout()
    response = flask.Response(response='LOGOUT_CONFIRMED')
    response.set_cookie('Authorization', '', expires=0)
    
    return response


@db_close
@handle_exception
@ensure_logged_in
def handle_new_token():
    payload = json.loads(request.data)
    if payload['context'] == 'world':
        character = psql_character_repository.get_character_by_field(
            'character_id', payload['id'], user_id=request.user['user_id']
        )
        character.ensure_can_authenticate()
        auth_response = auth_service.authenticate_character(character.as_dict(context='token'))
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
