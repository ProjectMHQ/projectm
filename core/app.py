import flask
from core.src.database import init_db, db
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

if __name__ == '__main__':
    app.run(debug=True, port=60160)
