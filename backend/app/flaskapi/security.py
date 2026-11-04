"""OAuth2 helpers used by Swagger Authorize and cookie/bearer auth."""

from __future__ import annotations

from dataclasses import dataclass

from app.flaskapi.request import Request, current_request


class OAuth2PasswordBearer:
    def __init__(
        self,
        tokenUrl: str,
        auto_error: bool = True,
        scheme_name: str | None = None,
        description: str | None = None,
    ):
        self.tokenUrl = tokenUrl
        self.auto_error = auto_error
        self.scheme_name = scheme_name
        self.description = description

    def __call__(self, request: Request | None = None) -> str | None:
        req = request or current_request()
        header = req.headers.get("authorization", "")
        if header.lower().startswith("bearer "):
            return header[7:].strip()
        return None


@dataclass
class OAuth2PasswordRequestForm:
    username: str
    password: str
    grant_type: str | None = None
    scope: str = ""
    client_id: str | None = None
    client_secret: str | None = None
