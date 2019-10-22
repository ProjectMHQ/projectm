import flask

bp = flask.Blueprint('system', __name__)


def ping():
    return flask.Response(response='PONG')


def serve_test_client():
    return flask.render_template('test_client.html')


bp.add_url_rule('/ping', view_func=ping, methods=['GET'])
bp.add_url_rule('/test_client', view_func=serve_test_client, methods=['GET'])
