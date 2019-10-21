import logging


class LoggingFactory(object):
    @staticmethod
    def _get_logger(name):
        return logging.getLogger(name)

    @property
    def core(self):
        return LoggingFactory._get_logger('core')


LOGGING_FACTORY = LoggingFactory()
