import logging


class LoggingFactory(object):
    @staticmethod
    def _get_logger(name):
        return logging.getLogger(name)

    @property
    def core(self):
        return LoggingFactory._get_logger('core')

    @property
    def websocket_monitor(self):
        return LoggingFactory._get_logger('websocket_monitor')


LOGGING_FACTORY = LoggingFactory()
