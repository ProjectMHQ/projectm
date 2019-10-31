class CoreException(Exception):
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


class BadRequest(CoreException):
    pass


class MethodNotAllowed(CoreException):
    pass


class InputValidationError(CoreException):
    pass


class InvalidTypeException(CoreException):
    pass


class ResourceNotFound(CoreException):
    pass


class ResourceUnprocessable(CoreException):
    pass


class ResourceDuplicated(CoreException):
    pass


class UnauthorizedError(CoreException):
    pass


class ForbiddenError(CoreException):
    pass


class InvalidPayloadException(CoreException):
    pass


class InvalidPasswordException(CoreException):
    pass


class InvalidRoleException(CoreException):
    pass


class EmailConfirmationTokenExpiredException(CoreException):
    pass


class AlreadyLoggedInException(CoreException):
    @property
    def status_code(self):
        return 401

    @property
    def message(self):
        return 'ALREADY_LOGGED_IN'


class NotLoggedInException(CoreException):
    @property
    def status_code(self):
        return 401

    @property
    def message(self):
        return 'NOT_LOGGED_IN'


class SessionExpiredException(CoreException):
    @property
    def status_code(self):
        return 401

    @property
    def message(self):
        return 'SESSION_EXPIRED'


