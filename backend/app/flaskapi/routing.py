"""APIRouter + dependency injection that keeps FastAPI-style endpoint signatures."""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Callable, get_args, get_origin

from flask import Response as FlaskResponse
from flask import g, jsonify, request as flask_request
from pydantic import BaseModel, ValidationError

from app.core.errors import ApiError, BadRequest, Unprocessable
from app.flaskapi.params import Depends, Param, RouteOptions
from app.flaskapi.request import Request
from app.flaskapi.response import FileResponse, Response, encode_result
from app.flaskapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


@dataclass
class Route:
    path: str
    methods: list[str]
    endpoint: Callable[..., Any]
    options: RouteOptions
    name: str
    openapi_extra: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class UploadFile:
    """Minimal UploadFile stand-in over Werkzeug FileStorage."""

    def __init__(self, storage):
        self._storage = storage
        self.filename = storage.filename
        self.content_type = storage.mimetype
        self.file = storage.stream

    def read(self, size: int = -1) -> bytes:
        return self._storage.read(size)


class ValidationFailed(ApiError):
    status_code = 422
    code = "validation_error"

    def __init__(self, message: str, *, fields: dict[str, str]):
        super().__init__(message, code="validation_error")
        self.fields = fields


def _flask_path(path: str) -> str:
    return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", r"<\1>", path)


def _is_model(annotation: Any) -> bool:
    try:
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)
    except TypeError:
        return False


def _annotation_model(annotation: Any) -> type[BaseModel] | None:
    if _is_model(annotation):
        return annotation
    origin = get_origin(annotation)
    if origin is list:
        args = get_args(annotation)
        if args and _is_model(args[0]):
            return args[0]
    return None


def _coerce(value: Any, annotation: Any) -> Any:
    if value is None or annotation is inspect.Parameter.empty or annotation is Any:
        return value
    origin = get_origin(annotation)
    args = [a for a in get_args(annotation) if a is not type(None)]
    target = args[0] if origin is not None and args else annotation
    if target is int:
        return int(value)
    if target is float:
        return float(value)
    if target is bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on"}
    try:
        from datetime import date, datetime

        if target is date:
            return date.fromisoformat(str(value))
        if target is datetime:
            return datetime.fromisoformat(str(value))
    except Exception:
        pass
    return value


def _validate_param(name: str, value: Any, info: Param) -> Any:
    if value is None:
        if info.required:
            raise BadRequest(f"Missing required parameter: {name}")
        return info.default
    if info.ge is not None and value < info.ge:
        raise Unprocessable(f"{name} must be >= {info.ge}")
    if info.le is not None and value > info.le:
        raise Unprocessable(f"{name} must be <= {info.le}")
    if info.min_length is not None and isinstance(value, str) and len(value) < info.min_length:
        raise Unprocessable(f"{name} is too short")
    if info.max_length is not None and isinstance(value, str) and len(value) > info.max_length:
        raise Unprocessable(f"{name} is too long")
    if info.pattern and isinstance(value, str) and re.fullmatch(info.pattern, value) is None:
        raise Unprocessable(f"{name} has an invalid format")
    return value


def _validation_error(exc: ValidationError) -> ValidationFailed:
    fields: dict[str, str] = {}
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", []) if p not in ("body", "query", "path"))
        fields[loc or "request"] = err.get("msg", "Invalid value")
    summary = "; ".join(f"{k}: {v}" for k, v in list(fields.items())[:3])
    return ValidationFailed(f"Validation failed ({summary})", fields=fields)


class APIRouter:
    def __init__(self, prefix: str = "", tags: list[str] | None = None):
        self.prefix = prefix.rstrip("/")
        self.tags = tags or []
        self.routes: list[Route] = []

    def add_api_route(self, path: str, endpoint: Callable[..., Any], *, methods: list[str], **kwargs):
        options = RouteOptions(
            response_model=kwargs.get("response_model"),
            status_code=kwargs.get("status_code", 200),
            summary=kwargs.get("summary"),
            description=kwargs.get("description"),
            openapi_extra=kwargs.get("openapi_extra"),
            tags=list(kwargs.get("tags") or self.tags),
            response_class=kwargs.get("response_class"),
        )
        route = Route(
            path=path if path.startswith("/") else f"/{path}",
            methods=[m.upper() for m in methods],
            endpoint=endpoint,
            options=options,
            name=endpoint.__name__,
            openapi_extra=options.openapi_extra or {},
            tags=options.tags,
        )
        endpoint.__bazaar_route__ = route  # type: ignore[attr-defined]
        self.routes.append(route)
        return endpoint

    def get(self, path: str, **kwargs):
        def deco(fn):
            return self.add_api_route(path, fn, methods=["GET"], **kwargs)

        return deco

    def post(self, path: str, **kwargs):
        def deco(fn):
            return self.add_api_route(path, fn, methods=["POST"], **kwargs)

        return deco

    def put(self, path: str, **kwargs):
        def deco(fn):
            return self.add_api_route(path, fn, methods=["PUT"], **kwargs)

        return deco

    def patch(self, path: str, **kwargs):
        def deco(fn):
            return self.add_api_route(path, fn, methods=["PATCH"], **kwargs)

        return deco

    def delete(self, path: str, **kwargs):
        def deco(fn):
            return self.add_api_route(path, fn, methods=["DELETE"], **kwargs)

        return deco


def _call_dependency(dep: Any, request: Request, cleanups: list[Any]) -> Any:
    if isinstance(dep, Depends):
        target = dep.dependency
    else:
        target = dep
    if target is None:
        return None
    if inspect.isgeneratorfunction(target):
        gen = target()
        value = next(gen)
        cleanups.append(gen)
        return value
    if isinstance(target, OAuth2PasswordBearer):
        return target(request)
    if inspect.isfunction(target) or inspect.ismethod(target):
        return _invoke_callable(target, request, {}, cleanups, allow_body=False)
    if callable(target):
        return target(request)
    return target


def _invoke_callable(
    fn: Callable[..., Any],
    request: Request,
    path_params: dict[str, Any],
    cleanups: list[Any],
    *,
    allow_body: bool,
) -> Any:
    sig = inspect.signature(fn)
    kwargs: dict[str, Any] = {}
    response_obj: Response | None = None

    for name, param in sig.parameters.items():
        ann = param.annotation
        default = param.default

        if isinstance(default, Depends):
            if default.dependency is None and (ann is OAuth2PasswordRequestForm or name in {"form", "data"}):
                kwargs[name] = OAuth2PasswordRequestForm(
                    username=(flask_request.form.get("username") or "").strip(),
                    password=flask_request.form.get("password") or "",
                )
                continue
            kwargs[name] = _call_dependency(default, request, cleanups)
            continue

        if isinstance(default, Param):
            info = default
            if info.kind == "query":
                raw = flask_request.args.get(info.alias or name)
                value = None if raw is None else _coerce(raw, ann)
                kwargs[name] = _validate_param(name, value, info)
            elif info.kind == "form":
                raw = flask_request.form.get(info.alias or name)
                value = None if raw is None else _coerce(raw, ann)
                kwargs[name] = _validate_param(name, value, info)
            elif info.kind == "file":
                storage = flask_request.files.get(info.alias or name)
                if storage is None or storage.filename in (None, ""):
                    if info.required:
                        raise BadRequest(f"Missing file: {name}")
                    kwargs[name] = None
                else:
                    kwargs[name] = UploadFile(storage)
            continue

        if ann is Request or name == "request":
            kwargs[name] = request
            continue

        if ann is Response:
            response_obj = response_obj or Response()
            kwargs[name] = response_obj
            continue

        if name in path_params:
            kwargs[name] = _coerce(path_params[name], ann)
            continue

        model = _annotation_model(ann) if allow_body else None
        if model is not None:
            payload = flask_request.get_json(silent=True)
            if payload is None:
                payload = {} if get_origin(ann) is not list else []
            try:
                if get_origin(ann) is list:
                    kwargs[name] = [model.model_validate(item) for item in payload]
                else:
                    kwargs[name] = model.model_validate(payload)
            except ValidationError as exc:
                raise _validation_error(exc) from exc
            continue

        # Plain scalar defaults behave like FastAPI query params (e.g. include_ended: bool = False).
        if default is not inspect.Parameter.empty:
            bare = ann
            if get_origin(ann) is not None:
                args = [a for a in get_args(ann) if a is not type(None)]
                bare = args[0] if len(args) == 1 else ann
            if bare in (bool, int, float, str):
                raw = flask_request.args.get(name)
                kwargs[name] = default if raw is None else _coerce(raw, bare)
            else:
                kwargs[name] = default
            continue

        raise BadRequest(f"Cannot resolve parameter '{name}' for {fn.__name__}")

    result = fn(**kwargs)
    if response_obj is not None:
        g._bazaar_response_obj = response_obj
    return result


def make_view(route: Route):
    def view(**path_params):
        from app.flaskapi.handlers import handle_exception

        request = Request()
        g._bazaar_path_params = path_params
        g._bazaar_response_obj = None
        g._bazaar_scope = {
            "route": SimpleNamespace(
                path=route.path,
                tags=route.tags,
                openapi_extra=route.openapi_extra,
                endpoint=route.endpoint,
                methods=route.methods,
                dependant=SimpleNamespace(
                    path_params=[SimpleNamespace(name=p) for p in re.findall(r"\{(\w+)\}", route.path)]
                ),
            ),
            "type": "http",
            "method": flask_request.method,
            "path": flask_request.path,
        }

        cleanups: list[Any] = []
        try:
            result = _invoke_callable(route.endpoint, request, path_params, cleanups, allow_body=True)
            return _finalize(result, route)
        except Exception as exc:
            return handle_exception(request, exc)
        finally:
            for gen in reversed(cleanups):
                try:
                    next(gen)
                except StopIteration:
                    pass
                except Exception:
                    try:
                        gen.close()
                    except Exception:
                        pass

    view.__name__ = f"{route.name}_{'_'.join(route.methods)}_{abs(hash(route.path + route.name)) % 10_000_000}"
    return view


def _finalize(result: Any, route: Route):
    status = route.options.status_code
    response_obj: Response | None = getattr(g, "_bazaar_response_obj", None)

    if isinstance(result, FileResponse):
        resp = result.to_flask()
        if response_obj:
            response_obj._apply_cookies(resp)
        return resp
    if isinstance(result, Response):
        if result.body is None and status == 204:
            result.status_code = 204
        return result.to_flask()
    if isinstance(result, FlaskResponse):
        if response_obj:
            response_obj._apply_cookies(result)
        return result

    if status == 204:
        resp = FlaskResponse(b"", status=204)
        if response_obj:
            response_obj._apply_cookies(resp)
        return resp

    payload = encode_result(result, route.options.response_model)
    resp = jsonify(payload)
    resp.status_code = status
    if response_obj:
        response_obj._apply_cookies(resp)
    return resp


def register_router(app, router: APIRouter) -> None:
    for route in router.routes:
        full = f"{router.prefix}{route.path}"
        rule = _flask_path(full)
        endpoint_name = f"{router.prefix}_{route.name}_{'_'.join(route.methods)}_{abs(hash(rule)) % 10_000_000}".replace("/", "_")
        app.add_url_rule(rule, endpoint=endpoint_name, view_func=make_view(route), methods=route.methods)
