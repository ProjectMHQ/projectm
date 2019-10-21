import flask

bp = flask.Blueprint('system', __name__)


def ping():
    return flask.Response(response='PONG')


bp.add_url_rule('/ping', view_func=ping, methods=['GET'])
