class AppError(Exception):
    pass

class ServiceError(AppError):
    pass

class TimedOutError(AppError):
    pass

class InvalidError(AppError):
    pass
