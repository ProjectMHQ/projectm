class coreException(Exception):
    def __init__(self, *a, **kw):
        self.kw = kw
        self.a = a
        super().__init__(*a)

    @property
    def message(self):
        return self.kw.get('message')

    @property
    def status_code(self):
        return int(self.kw.get('status_code', 400))


class BadRequest(coreException):
    pass


class MethodNotAllowed(coreException):
    pass


class InputValidationError(coreException):
    pass


class InvalidTypeException(coreException):
    pass


class ResourceNotFound(coreException):
    pass


class ResourceUnprocessable(coreException):
    pass


class ResourceDuplicated(coreException):
    pass


class UnauthorizedError(coreException):
    pass


class ForbiddenError(coreException):
    pass


class InvalidPayloadException(coreException):
    pass


class InvalidPasswordException(coreException):
    pass


class InvalidRoleException(coreException):
    pass


class EmailConfirmationTokenExpiredException(coreException):
    pass


class AlreadyLoggedInException(coreException):
    @property
    def status_code(self):
        return 401

    @property
    def message(self):
        return 'ALREADY_LOGGED_IN'


class NotLoggedInException(coreException):
    @property
    def status_code(self):
        return 401

    @property
    def message(self):
        return 'NOT_LOGGED_IN'


class SessionExpiredException(coreException):
    @property
    def status_code(self):
        return 401

    @property
    def message(self):
        return 'SESSION_EXPIRED'


