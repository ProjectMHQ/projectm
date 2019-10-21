import typing
import flask
from functools import wraps
from werkzeug.routing import UUIDConverter

from core.src.exceptions import coreException


def handle_exception(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        try:
            return fun(*a, **kw)
        except coreException as e:
            return flask.Response(response=e.message, status=e.status_code)
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
