"""Response helpers compatible with FastAPI Response / FileResponse usage."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from flask import Response as FlaskResponse
from flask import send_file
from pydantic import BaseModel


class Response:
    """Mutable response used by auth cookie helpers and raw CSV downloads."""

    def __init__(
        self,
        content: Any = None,
        *,
        status_code: int = 200,
        media_type: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.body = content
        self.status_code = status_code
        self.media_type = media_type or "application/json"
        self.headers: dict[str, str] = dict(headers or {})
        self._cookies: list[dict[str, Any]] = []
        self._delete_cookies: list[dict[str, Any]] = []

    def set_cookie(self, key: str, value: str = "", **kwargs):
        self._cookies.append({"key": key, "value": value, **kwargs})

    def delete_cookie(self, key: str, **kwargs):
        self._delete_cookies.append({"key": key, **kwargs})

    def to_flask(self) -> FlaskResponse:
        body = self.body
        if isinstance(body, (dict, list)):
            from app.flaskapi.encoding import jsonable_encoder
            import json

            payload = json.dumps(jsonable_encoder(body))
            resp = FlaskResponse(payload, status=self.status_code, mimetype=self.media_type)
        elif body is None or body == b"":
            resp = FlaskResponse(b"", status=self.status_code, mimetype=self.media_type)
        elif isinstance(body, (bytes, bytearray)):
            resp = FlaskResponse(bytes(body), status=self.status_code, mimetype=self.media_type)
        else:
            resp = FlaskResponse(str(body), status=self.status_code, mimetype=self.media_type)
        for k, v in self.headers.items():
            resp.headers[k] = v
        self._apply_cookies(resp)
        return resp

    def _apply_cookies(self, resp: FlaskResponse) -> None:
        for item in self._cookies:
            key = item.pop("key")
            value = item.pop("value")
            # Flask uses max_age; FastAPI-compatible kwargs.
            max_age = item.pop("max_age", None)
            httponly = item.pop("httponly", False)
            samesite = item.pop("samesite", None)
            secure = item.pop("secure", False)
            path = item.pop("path", "/")
            resp.set_cookie(
                key,
                value,
                max_age=max_age,
                httponly=httponly,
                samesite=samesite,
                secure=secure,
                path=path,
            )
        for item in self._delete_cookies:
            key = item.pop("key")
            path = item.pop("path", "/")
            resp.delete_cookie(key, path=path)


class FileResponse(Response):
    def __init__(
        self,
        path: str | Path,
        *,
        media_type: str | None = None,
        filename: str | None = None,
        content_disposition_type: str = "attachment",
        headers: dict[str, str] | None = None,
        status_code: int = 200,
    ):
        super().__init__(status_code=status_code, media_type=media_type, headers=headers)
        self.path = Path(path)
        self.filename = filename or self.path.name
        self.content_disposition_type = content_disposition_type

    def to_flask(self) -> FlaskResponse:
        mime = self.media_type or mimetypes.guess_type(str(self.path))[0] or "application/octet-stream"
        resp = send_file(
            self.path,
            mimetype=mime,
            as_attachment=self.content_disposition_type == "attachment",
            download_name=self.filename,
            conditional=True,
        )
        for k, v in self.headers.items():
            resp.headers[k] = v
        self._apply_cookies(resp)
        return resp


def encode_result(result: Any, response_model: Any = None) -> Any:
    from app.flaskapi.encoding import jsonable_encoder

    if result is None:
        return None
    if isinstance(result, (Response, FileResponse, FlaskResponse)):
        return result
    if isinstance(result, BaseModel):
        return jsonable_encoder(result.model_dump(mode="json"))
    if isinstance(result, list) and result and isinstance(result[0], BaseModel):
        return [jsonable_encoder(item.model_dump(mode="json")) for item in result]
    return jsonable_encoder(result)
