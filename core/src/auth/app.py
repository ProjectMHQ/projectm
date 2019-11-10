import flask
from flask_cors import CORS
from flask.logging import default_handler
from werkzeug.exceptions import HTTPException

from core.src.auth.database import init_db, db
from core.src.auth.exceptions import CoreException
from core.src.auth.logging_factory import LOGGER
from core.src.auth.utils import FlaskUUID

from core.src.auth.router.auth import bp as auth_bp
from core.src.auth.router.system import bp as system_bp
from core.src.auth.router.user import bp as user_bp
from etc import settings


app = flask.Flask(__name__)
app.logger.removeHandler(default_handler)
FlaskUUID(app)


if settings.ENABLE_CORS:
    CORS(app=app, supports_credentials=True)

app.config.update(
    DEBUG=True,
    TESTING=True,
    SECRET_KEY='cafebabedeadbeef'
)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(system_bp, url_prefix='/system')
app.register_blueprint(user_bp, url_prefix='/user')
app.add_url_rule('/favicon.ico', 'favico', lambda *a, **kw: '')


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
    if isinstance(exception, HTTPException):
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
    app.run(
        port=int(settings.WEB_PORT),
        host=settings.WEB_HOSTNAME,
        debug=settings.DEBUG
    )
