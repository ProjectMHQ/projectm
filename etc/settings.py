import binascii
import hashlib

ENV = 'development'
RUNNING_TESTS = False
ENCRYPTION_KEY = b'12345678'
ENCRYPTION_IV = hashlib.md5('$$$ initial value seed'.encode()).digest()
WEB_PROTOCOL = 'http'
WEB_BASE_HOSTNAME = 'localhost'
WEB_BASE_PORT = 60160

WEB_BASE_URL = '{}://{}:{}'.format(WEB_PROTOCOL, WEB_BASE_HOSTNAME, WEB_BASE_PORT)

#SQL_DRIVER = 'postgresql'
SQL_DRIVER = 'sqlite'

POSTGRESQL_USERNAME = 'user'
POSTGRESQL_PASSWORD = 'pass'
POSTGRESQL_HOSTNAME = 'localhost'
POSTGRESQL_DATABASE = 5432
SQLITE_DB = '/tmp/core.db'

if SQL_DRIVER == 'postgresql':
    DATASOURCE = 'postgresql://{}:{}@{}/{}'.format(
        POSTGRESQL_USERNAME,
        POSTGRESQL_PASSWORD,
        POSTGRESQL_HOSTNAME,
        POSTGRESQL_DATABASE
    )
elif SQL_DRIVER == 'sqlite':
    DATASOURCE = 'sqlite:///{}'.format(SQLITE_DB)

USE_SQLITE = True

EMAIL_CONFIRMATION_LINK_TTL = 3600 * 24
EMAIL_MUST_BE_CONFIRMED = True

SENDGRID_API_KEY = 'SG.fNKabwGwTXOutmjViiVDEQ.upJZx59daaaaacECmSfFZcWjZoLhJxbIECm5D_evVYjVDR0 '

TOKEN_TTL = 3600 * 6