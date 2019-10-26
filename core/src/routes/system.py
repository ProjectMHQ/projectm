import flask
from etc import settings

bp = flask.Blueprint('system', __name__)


def ping():
    return flask.Response(response='PONG')


def serve_test_client():
    return flask.render_template(
        'test_client.html',
        context={
            'ws_host': settings.WEB_BASE_HOSTNAME,
            'ws_port': settings.WEB_BASE_PORT
        }
    )


def serve_dashboard():
    return flask.render_template('index.html')


bp.add_url_rule('/ping', view_func=ping, methods=['GET'])
bp.add_url_rule('/test_client', view_func=serve_test_client, methods=['GET'])
bp.add_url_rule('/dashboard', view_func=serve_dashboard, methods=['GET'])
