import eventlet
from eventlet.green.http.client import HTTPException as EventletHTTPException
from werkzeug.exceptions import HTTPException as WerkzeugHTTPException
eventlet.monkey_patch()

import flask
from flask.logging import default_handler
from flask_socketio import SocketIO
from core.src.database import init_db, db
from core.src.exceptions import CoreException
from core.src.logging_factory import LOGGER
from core.src.router.websocket import build_base_websocket_route
from core.src.utils import FlaskUUID

from core.src.router.auth import bp as auth_bp
from core.src.router.system import bp as system_bp
from core.src.router.user import bp as user_bp
from etc import settings


app = flask.Flask(__name__)
app.logger.removeHandler(default_handler)
FlaskUUID(app)


socketion_settings = {
    'async_mode': 'eventlet'
}

if settings.ENABLE_CORS:
    socketion_settings['cors_allowed_origins'] = "*"

    @app.after_request
    def after_request(response):
        header = response.headers
        header['Access-Control-Allow-Origin'] = '*'
        header['Access-Control-Allow-Headers'] = '*'
        return response


app.config.update(
    DEBUG=True,
    TESTING=True,
    SECRET_KEY='cafebabedeadbeef'
)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(system_bp, url_prefix='/system')
app.register_blueprint(user_bp, url_prefix='/user')
app.add_url_rule('/favicon.ico', 'favico', lambda *a, **kw: '')

socketio = SocketIO(app, message_queue='redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT))


socketio.init_app(app, **socketion_settings)

build_base_websocket_route(socketio)


@app.before_request
def _init_db():
    init_db(db)


@app.teardown_request
def _tear_db(response):
    # noinspection PyBroadException
    try:
        db().close()
    except:
        LOGGER.core.exception('Error closing database')
    return response


@app.after_request
def _tear_cors(response):
    if settings.ENABLE_CORS:
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        response.headers['Access-Control-Expose-Headers'] = '*'
    return response


@app.errorhandler(CoreException)
def core_handler(exception):
    LOGGER.core.exception('Exception caught')
    return flask.Response(
        response=str(exception),
        status=getattr(exception, 'status_code', 400)
    )


@app.errorhandler(Exception)
def all_exceptions_handler(exception):
    LOGGER.core.exception('Exception caught')
    if isinstance(exception, EventletHTTPException) \
            or isinstance(exception, WerkzeugHTTPException):
        return flask.Response(
            response=exception.description,
            status=exception.code
        )

    return flask.Response(
        response=getattr(exception, 'description', str(exception)),
        status=getattr(exception, 'code', 500),
    )


if __name__ == '__main__':
    LOGGER.core.error('Starting')
    socketio.run(
        app,
        port=int(settings.WEB_PORT),
        host=settings.WEB_HOSTNAME,
        debug=settings.DEBUG
    )
