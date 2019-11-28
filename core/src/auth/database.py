from functools import wraps
import sqlalchemy
from sqlalchemy import create_engine, exc, event
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from etc import settings
import threading
import json

_threadlocal = threading.local()


if settings.SQL_DRIVER == 'postgresql':
    from sqlalchemy.dialects import postgresql
    json_column_type = postgresql.JSONB
    _engine_endpoint = settings.DATASOURCE

elif settings.SQL_DRIVER == 'sqlite' or settings.RUNNING_TESTS:
    class JsonEncodedDict(sqlalchemy.TypeDecorator):
        impl = sqlalchemy.String

        def process_bind_param(self, value, dialect):
            return json.dumps(value)

        def process_result_value(self, value, dialect):
            return json.loads(value)


    from sqlalchemy.ext import mutable
    mutable.MutableDict.associate_with(JsonEncodedDict)
    json_column_type = JsonEncodedDict
    _engine_endpoint = settings.DATASOURCE
else:
    raise ValueError('unknown driver')


engine = create_engine(_engine_endpoint, convert_unicode=True)


@event.listens_for(engine, "engine_connect")
def ping_connection(connection, branch):
    if branch:
        return

    save_should_close_with_result = connection.should_close_with_result
    connection.should_close_with_result = False

    try:
        connection.scalar(sqlalchemy.select([1]))
    except exc.DBAPIError as err:
        if err.connection_invalidated:
            connection.scalar(sqlalchemy.select([1]))
        else:
            raise
    finally:
        connection.should_close_with_result = save_should_close_with_result


db = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db.query_property()


def init_db(_db):
    _threadlocal.db = _db


def atomic(fun):
    @wraps(fun)
    def _inner_atomic(*args, **kwargs):
        try:
            try:
                _threadlocal.counter += 1
            except AttributeError:
                _threadlocal.counter = 1
            r = fun(*args, **kwargs)
            if _threadlocal.counter == 1:
                _threadlocal.db.commit()
            _threadlocal.counter -= 1
            return r
        except Exception as e:
            raise e

    return _inner_atomic


def db_close(fun):
    @wraps(fun)
    def wrapper(*a, **kw):
        r = fun(*a, **kw)
        _threadlocal.db.close()
        return r
    return wrapper
