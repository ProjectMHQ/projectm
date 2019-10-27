import hashlib
import os
from configparser import ConfigParser

ENV = os.environ['PROJECTM_ENV']
RUNNING_TESTS = os.environ.get('RUNNING_TESTS')
INI_FILE = os.path.join(os.path.dirname(__file__), ENV, 'settings.conf')
LOCAL_SETTINGS_INI_FILE = os.path.join(os.path.dirname(__file__), ENV, 'local-settings.conf')

config = ConfigParser()
config.read(INI_FILE)
config.read(LOCAL_SETTINGS_INI_FILE)

DEBUG = config['settings']['debug']

ENCRYPTION_KEY = hashlib.sha256(config['settings']['encryption_key_seed'].encode()).digest()
ENCRYPTION_IV = hashlib.md5(config['settings']['encryption_iv_seed'].encode()).digest()

WEB_PROTOCOL = config['settings']['web_protocol']
WEB_HOSTNAME = config['settings']['web_hostname']
WEB_PORT = config['settings']['web_port']

SOCKETIO_HOSTNAME = config['settings']['socketio_hostname']
SOCKETIO_PORT = config['settings']['socketio_port']

WEB_BASE_URL = '{}://{}:{}'.format(WEB_PROTOCOL, WEB_HOSTNAME, WEB_PORT)

SQL_DRIVER = config['database']['sql_driver']

POSTGRESQL_USERNAME = config['database']['postgresql_username']
POSTGRESQL_PASSWORD = config['database']['postgresql_password']
POSTGRESQL_HOSTNAME = config['database']['postgresql_hostname']
POSTGRESQL_DATABASE = config['database']['postgresql_database']
POSTGRESQL_PORT = int(config['database'].get('postgresql_port') or 0)

SQLITE_DB = config['database']['sqlite_db_file']

if SQL_DRIVER == 'postgresql':
    DATASOURCE = 'postgresql://{}:{}@{}:{}/{}'.format(
        POSTGRESQL_USERNAME,
        POSTGRESQL_PASSWORD,
        POSTGRESQL_HOSTNAME,
        POSTGRESQL_PORT,
        POSTGRESQL_DATABASE
    )
elif SQL_DRIVER == 'sqlite':
    DATASOURCE = 'sqlite:///{}'.format(SQLITE_DB)

EMAIL_CONFIRMATION_LINK_TTL = config['settings'].getint('email_confirmation_link_ttl')
EMAIL_MUST_BE_CONFIRMED = config['settings'].getboolean('email_must_be_confirmed')

SENDGRID_API_KEY = config['settings']['sendgrid_api_key']

TOKEN_TTL = int(config['settings'].getint('token_ttl'))

ENABLE_CORS = config['settings']['enable_cors']

REDIS_HOST = config['database']['redis_host']
REDIS_PORT = int(config['database']['redis_port'] or 0)
REDIS_DB = int(config['database']['redis_db'] or 0)

FLUENTD_HANDLER_HOST = config['logging']['fluentd_host']
FLUENTD_HANDLER_PORT = config['logging']['fluentd_port']

