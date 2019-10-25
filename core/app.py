import flask
from flask_socketio import SocketIO
from core.src.database import init_db, db
from core.src.exceptions import ResourceDuplicated
from core.src.routes.websocket import build_websocket_route
from core.src.utils.tools import FlaskUUID

from core.src.routes.auth import bp as auth_bp
from core.src.routes.system import bp as system_bp
from core.src.routes.user import bp as user_bp
from etc import settings


app = flask.Flask(__name__)
FlaskUUID(app)


socketion_settings = {}

if settings.ENABLE_CORS:
    socketion_settings['cors_allowed_origins'] = "*"

    @app.after_request
    def after_request(response):
        header = response.headers
        header['Access-Control-Allow-Origin'] = '*'
        return response


app.config.update(
    DEBUG=True,
    TESTING=True,
    SECRET_KEY='cafebabedeadbeef'
)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(system_bp, url_prefix='/system')
app.register_blueprint(user_bp, url_prefix='/user')
socketio = SocketIO(app)


socketio.init_app(app, **socketion_settings)

build_websocket_route(socketio)


@app.before_request
def _init_db():
    init_db(db)


@app.errorhandler(ResourceDuplicated)
def handler(exception):
    return flask.Response(
        response=str(exception),
        status=getattr(exception, 'status_code', 400)
    )


if __name__ == '__main__':
    socketio.run(app, port=60160, debug=True)
