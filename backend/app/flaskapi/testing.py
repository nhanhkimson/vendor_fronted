"""Test client with a FastAPI TestClient-like surface for existing pytest helpers."""

from __future__ import annotations

from typing import Any

from flask import Flask


class _Resp:
    def __init__(self, response):
        self._response = response
        self.status_code = response.status_code
        self.content = response.data
        self.text = response.get_data(as_text=True)
        self.headers = {k: v for k, v in response.headers.items()}

    def json(self):
        return self._response.get_json(silent=False)


class TestClient:
    def __init__(self, app: Flask):
        self.app = app
        self._ctx = app.app_context()
        self._client = app.test_client()

    def __enter__(self):
        self._ctx.push()
        return self

    def __exit__(self, *args):
        self._ctx.pop()
        return False

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        content_type: str | None = None,
        **kwargs,
    ):
        hdrs = dict(headers or {})
        if json is not None:
            response = self._client.open(path, method=method.upper(), json=json, headers=hdrs, **kwargs)
        else:
            response = self._client.open(
                path,
                method=method.upper(),
                data=data,
                headers=hdrs,
                content_type=content_type,
                **kwargs,
            )
        return _Resp(response)

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)
