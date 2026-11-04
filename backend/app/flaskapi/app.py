"""Flask application factory for the Bazaar API."""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from app.core.config import settings
from app.flaskapi.middleware import install_middleware
from app.flaskapi.routing import register_router

log = logging.getLogger("bazaar")


def create_app() -> Flask:
    app = Flask("bazaar-api")
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_bytes + 1024
    install_middleware(app)

    from app.routers import ROUTERS

    for router in ROUTERS:
        register_router(app, router)

    media_root = Path(settings.media_dir)
    media_root.mkdir(parents=True, exist_ok=True)

    @app.get("/media/<path:filename>")
    def media(filename: str):
        return send_from_directory(media_root, filename)

    @app.get("/api/openapi.json")
    def openapi():
        return jsonify(build_openapi(app))

    @app.get("/api/docs")
    def docs():
        html = """<!DOCTYPE html>
<html>
<head>
  <title>Bazaar Marketplace API</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({
      url: '/api/openapi.json',
      dom_id: '#swagger-ui',
      persistAuthorization: true,
      tryItOutEnabled: true,
      docExpansion: 'none',
      filter: true,
      displayRequestDuration: true,
    });
  </script>
</body>
</html>"""
        return html

    @app.get("/api/redoc")
    def redoc():
        return (
            "<!DOCTYPE html><html><head><title>Bazaar API</title>"
            '<script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>'
            "</head><body><redoc spec-url='/api/openapi.json'></redoc></body></html>"
        )

    return app


def build_openapi(app: Flask) -> dict:
    paths: dict = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith("static") or rule.rule in {"/api/docs", "/api/redoc", "/api/openapi.json"}:
            continue
        if not rule.rule.startswith("/api"):
            continue
        methods = [m for m in rule.methods if m in {"GET", "POST", "PUT", "PATCH", "DELETE"}]
        if not methods:
            continue
        path = rule.rule
        for converter, _, variable in getattr(rule, "_trace", []) if False else []:
            pass
        # Convert Flask <id> to OpenAPI {id}
        import re

        oa_path = re.sub(r"<([^:>]+:)?([^>]+)>", r"{\2}", path)
        item = paths.setdefault(oa_path, {})
        for method in methods:
            item[method.lower()] = {
                "summary": rule.endpoint,
                "responses": {"200": {"description": "OK"}},
            }
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Bazaar Marketplace API",
            "version": "1.0.0",
            "description": "Flask port of the Bazaar multi-vendor marketplace API.",
        },
        "paths": paths,
        "components": {
            "securitySchemes": {
                "Bazaar login": {
                    "type": "oauth2",
                    "flows": {
                        "password": {
                            "tokenUrl": "/api/auth/token",
                            "scopes": {},
                        }
                    },
                }
            }
        },
        "security": [{"Bazaar login": []}],
    }
