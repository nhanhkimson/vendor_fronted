"""Flask request adapter with FastAPI-like `.state` / `.client` / `.path_params`."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from flask import g, has_request_context, request as flask_request


class Client:
    def __init__(self, host: str | None):
        self.host = host or "unknown"


class Request:
    """Thin wrapper so services/deps keep using `request.state`, headers, cookies."""

    def __init__(self, environ_request=None):
        self._req = environ_request or flask_request

    @property
    def state(self) -> SimpleNamespace:
        if not hasattr(g, "_bazaar_state"):
            g._bazaar_state = SimpleNamespace()
        return g._bazaar_state

    @property
    def headers(self):
        return self._req.headers

    @property
    def cookies(self):
        return self._req.cookies

    @property
    def method(self) -> str:
        return self._req.method

    @property
    def url(self):
        return self._req.url

    @property
    def path_params(self) -> dict[str, Any]:
        return getattr(g, "_bazaar_path_params", {}) or {}

    @property
    def client(self) -> Client:
        return Client(self._req.remote_addr)

    @property
    def scope(self) -> dict[str, Any]:
        # Used by audit failure handler for route metadata.
        return getattr(g, "_bazaar_scope", {}) or {}


def current_request() -> Request:
    if not has_request_context():
        raise RuntimeError("No Flask request context")
    return Request()
