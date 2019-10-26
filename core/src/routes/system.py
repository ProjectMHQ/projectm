import flask

from core.src.authentication.scope import ensure_logged_in

bp = flask.Blueprint('system', __name__)


def ping():
    return flask.Response(response='PONG')


#@ensure_logged_in
def serve_test_client():
    return flask.render_template('test_client.html')


def serve_dashboard():
    return flask.render_template('index.html')


bp.add_url_rule('/ping', view_func=ping, methods=['GET'])
bp.add_url_rule('/test_client', view_func=serve_test_client, methods=['GET'])
bp.add_url_rule('/dashboard', view_func=serve_dashboard, methods=['GET'])
