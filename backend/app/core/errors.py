from typing import Any


class ApiError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, code: str | None = None, details: Any = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details


class BadRequest(ApiError):
    status_code = 400
    code = "bad_request"


class Unauthorized(ApiError):
    status_code = 401
    code = "not_authenticated"


class PaymentDeclined(ApiError):
    status_code = 402
    code = "payment_declined"


class Forbidden(ApiError):
    status_code = 403
    code = "forbidden"


class NotFound(ApiError):
    status_code = 404
    code = "not_found"

    def __init__(self, resource: str, resource_id: Any = None, **kwargs):
        label = f"{resource} {resource_id}" if resource_id is not None else resource
        super().__init__(f"{label} was not found", **kwargs)


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class Unprocessable(ApiError):
    status_code = 422
    code = "invalid"


class TooManyRequests(ApiError):
    status_code = 429
    code = "rate_limited"
