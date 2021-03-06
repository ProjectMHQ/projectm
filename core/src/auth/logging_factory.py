import logging
import sys
from core.src.auth.utils import get_current_user_id
from etc import settings


def _init_logging(loggers):
    if settings.RUNNING_TESTS:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler(sys.stdout))
        return
    if settings.ENV == 'development':
        for _n, _l in loggers.items():
            logging.basicConfig(level=getattr(logging, _l))
            _logger = logging.getLogger(_n)
            _logger.addHandler(logging.StreamHandler(sys.stdout))
            #_logger.addHandler(logging.StreamHandler(sys.stderr))

    if settings.FLUENTD_HANDLER_HOST:
        from fluent import handler
        import msgpack
        from io import BytesIO

        def overflow_handler(pendings):
            unpacker = msgpack.Unpacker(BytesIO(pendings))
            for unpacked in unpacker:
                print(unpacked)

        custom_format = {
          'host': '%(hostname)s',
          'where': '%(module)s.%(funcName)s',
          'type': '%(levelname)s',
          'stack_trace': '%(exc_text)s',
          'user_id': '%(user_id)s'
        }
        for _n, _l in loggers.items():
            logging.basicConfig(level=getattr(logging, _l))
            _handler = handler.FluentHandler(
                'app',
                host=settings.FLUENTD_HANDLER_HOST,
                port=int(settings.FLUENTD_HANDLER_PORT),
                buffer_overflow_handler=overflow_handler
            )
            _handler.setFormatter(handler.FluentRecordFormatter(custom_format, fill_missing_fmt_key=True))
            _logger = logging.getLogger(_n)
            _logger.addHandler(_handler)
            _logger.setLevel(getattr(logging, _l))
            _logger.error('Logging initialized')

        return


class LoggingFactory(object):
    def __init__(self):
        self.loggers = {
            'core': 'DEBUG',
            'websocket_monitor': 'DEBUG',
            'engineio.server': 'WARNING',
            'flask*': 'DEBUG',
            'testing': 'DEBUG'
        }
        _init_logging(self.loggers)

    @staticmethod
    def _get_logger(name):
        return logging.getLogger(name)

    @property
    def core(self):
        return logging.LoggerAdapter(
            logging.getLogger('core'),
            {"user_id": get_current_user_id()}
        )

    @property
    def websocket_monitor(self):
        return LoggingFactory._get_logger('websocket_monitor')

    @property
    def testing(self):
        return LoggingFactory._get_logger('testing')


LOGGER = LoggingFactory()
