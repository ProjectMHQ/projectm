import typing
from functools import wraps
from flask import request
from core.src import exceptions


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
        from core.src.builder import user_service
        if request and request.cookies and request.cookies.get('Authorization') and user_service.decode_session_token(
            request.cookies['Authorization'].replace('Bearer ', '')
        ):
            raise exceptions.AlreadyLoggedInException()
        return fun(*a, **kw)
    return wrapper


def ensure_logged_in(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        from core.src.builder import user_service
        if not request or not request.cookies or not request.cookies.get('Authorization'):
            raise exceptions.NotLoggedInException()
        session_token = user_service.decode_session_token(
            request.cookies['Authorization'].replace('Bearer ', '')
        )
        request.user = session_token['user']
        return fun(*a, **kw)
    return wrapper
