import json

import flask
from flask import request

from core.src.authentication.scope import ensure_not_logged_in, ensure_logged_in
from core.src.builder import user_service
from core.src.database import db_close
from core.src.utils.tools import handle_exception

bp = flask.Blueprint('auth', __name__)


@db_close
@handle_exception
@ensure_not_logged_in
def handle_email_address_confirmation(email_token):
    user_service.confirm_email_address(email_token)
    return flask.Response(response='EMAIL_CONFIRMED')


@db_close
@handle_exception
@ensure_not_logged_in
def handle_signup():
    payload = json.loads(request.data)
    user_service.signup(payload.get('email'), payload.get('password'))
    return flask.Response(response='SIGNUP_CONFIRMED')


@db_close
@handle_exception
@ensure_not_logged_in
def handle_login():
    payload = json.loads(request.data)
    login_response = user_service.login(payload.get('email'), payload.get('password'))
    response = flask.jsonify({"user_id": login_response['user_id']})
    response.set_cookie('Authorization', 'Bearer {}'.format(login_response['token']))
    return response


@db_close
@handle_exception
@ensure_logged_in
def handle_logout():
    user_service.logout()
    return flask.Response(response='LOGOUT_CONFIRMED')


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
