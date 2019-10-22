import flask
from flask_socketio import SocketIO
from core.src.database import init_db, db
from core.src.routes.websocket import build_websocket_route
from core.src.utils.tools import FlaskUUID
from core.src.routes.auth import bp as auth_bp
from core.src.routes.system import bp as system_bp


app = flask.Flask(__name__)
FlaskUUID(app)

app.config.update(
    DEBUG=True,
    TESTING=True,
    SECRET_KEY='cafebabedeadbeef'
)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(system_bp, url_prefix='/system')

init_db(db)

socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")
build_websocket_route(socketio)

if __name__ == '__main__':
    socketio.run(app, port=60160, debug=True)
