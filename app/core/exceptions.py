class AppError(Exception):
    pass

class ServiceError(AppError):
    pass

class TimedOutError(AppError):
    pass

class InvalidError(AppError):
    pass

class ProviderAuthError(ServiceError):
    pass

class ProviderRateLimitError(ServiceError):
    pass

class ProviderInvalidModelError(InvalidError):
    pass
