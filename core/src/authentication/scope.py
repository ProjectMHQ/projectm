import typing
from functools import wraps
from flask import request
from core.src import exceptions
from core.src.business.character.character import CharacterDOImpl


def get_current_user_id():
    if getattr(request, 'user', None):
        return request.user.user_id


def get_current_user():
    if getattr(request, 'user', None):
        return request.user


def get_roles() -> typing.List[str]:
    user = get_current_user()
    return user and user['roles'] or []


def ensure_not_logged_in(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        from core.src.builder import auth_service
        if request and request.cookies and request.cookies.get('Authorization') and auth_service.decode_session_token(
            request.cookies['Authorization'].replace('Bearer ', '')
        ):
            pass
        return fun(*a, **kw)
    return wrapper


def ensure_logged_in(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        from core.src.builder import auth_service
        if not request or not request.cookies or not request.cookies.get('Authorization'):
            raise exceptions.NotLoggedInException()
        session_token = auth_service.decode_session_token(
            request.cookies['Authorization'].replace('Bearer ', '')
        )
        request.user = session_token['user']
        response = fun(*a, **kw)
        for c in response.headers.get('Set-Cookie', []):
            if 'Cookie Authorization' in str(c):
                return response

        response.set_cookie('Authorization', request.cookies['Authorization'])
        return response
    return wrapper


def ensure_websocket_authentication(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        from core.src.builder import auth_service
        if not request or not request.cookies or not request.cookies.get('Authorization'):
            raise exceptions.NotLoggedInException()
        session_token = auth_service.decode_session_token(
            request.cookies['WS-Authorization'].replace('Bearer ', '')
        )
        if session_token['context'] != 'character':
            raise NotImplementedError('wtf?')

        request.character = CharacterDOImpl.from_session_token(session_token['data'])
        response = fun(*a, **kw)
        response.set_cookie('Authorization', request.cookies['Authorization'])
        response.set_cookie('WS-Authorization', request.cookies['WS-Authorization'])
        return response
    return wrapper
