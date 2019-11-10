import typing
from functools import wraps
from flask import request
from werkzeug.routing import UUIDConverter
from core.src.auth import exceptions


def deserialize_message(deserializer):
    def _fn(fun):
        @wraps(fun)
        async def wrapper(*a, **kw):
            from core.src.auth.logging_factory import LOGGER
            LOGGER.core.debug('deserialize_message: %s, %s', deserializer, a)
            return await fun(a[0], deserializer(a[1]), **kw)
        return wrapper
    return _fn


def get_current_user_id():
    try:
        if getattr(request, 'user', None):
            return request.user['user_id']
    except RuntimeError:
        return None


def get_current_user():
    if getattr(request, 'user', None):
        return request.user


def get_roles() -> typing.List[str]:
    user = get_current_user()
    return user and user['roles'] or []


def ensure_not_logged_in(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        from core.src.auth.builder import auth_service
        from core.src.auth.logging_factory import LOGGER
        LOGGER.core.debug('ensure_not_logged_in. path: %s request.cookies: %s', request.path, request.cookies)
        if request and request.cookies and request.cookies.get('Authorization') and auth_service.decode_session_token(
            request.cookies['Authorization'].replace('Bearer ', '')
        ):
            pass
        return fun(*a, **kw)
    return wrapper


def ensure_logged_in(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        from core.src.auth.logging_factory import LOGGER
        LOGGER.core.debug('ensure_logged_in, path: %s, request.cookies: %s', request.path, request.cookies)
        from core.src.auth.builder import auth_service
        if not request or not request.cookies or not request.cookies.get('Authorization'):
            raise exceptions.NotLoggedInException()
        session_token = auth_service.decode_session_token(request.cookies['Authorization'].replace('Bearer ', ''))
        request.user = session_token['user']
        response = fun(*a, **kw)
        return response
    return wrapper


def ensure_websocket_authentication(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        from core.src.auth.logging_factory import LOGGER
        LOGGER.core.debug(
            'ensure_websocket_authentication, path: %s request.cookies: %s', request.path, request.cookies
        )
        from core.src.auth.builder import auth_service
        if not request or not request.cookies or not request.cookies.get('Authorization'):
            raise exceptions.NotLoggedInException()
        user_token = auth_service.decode_session_token(request.cookies['Authorization'].replace('Bearer ', ''))
        request.user_token = user_token
        fun(*a, **kw)
    return wrapper


def namedtuple_to_dict(data: typing.NamedTuple):
    res = {}
    for field in data._fields:
        res[field] = getattr(data, field)
    return res


class FlaskUUID(object):
    """Flask extension providing a UUID url converter"""
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.url_map.converters['uuid'] = UUIDConverter
