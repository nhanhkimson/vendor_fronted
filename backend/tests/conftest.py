"""Pytest against bazaar_test as bazaar_app, so grants and row-level security are real."""

from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

import tests._env  # noqa: F401  — environment must be set before app settings load
from alembic import command
from app.core.config import settings
from app.core.middleware import AUDIT_VIOLATIONS
from app.main import app
from app.seed.run import reset_database

BACKEND = Path(__file__).resolve().parents[1]
ACCOUNTS = {
    "maya": "maya@bazaar.local",
    "jess": "jess@annescraftworks.local",
    "kein": "kein@keinmaker.local",
    "ava": "ava@bazaar.local",
    "daniel": "daniel@bazaar.local",
    "lin": "lin@bazaar.local",
    "theo": "theo@mail.local",
}


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def call(client: TestClient, method: str, path: str, token: str | None = None, json=None, ok: int | tuple = 200):
    response = client.request(method, path, headers=auth(token) if token else None, json=json)
    expected = (ok,) if isinstance(ok, int) else ok
    assert response.status_code in expected, f"{method} {path} -> {response.status_code}\n{response.text}"
    if response.status_code == 204 or not response.content:
        return response
    if "json" in response.headers.get("content-type", ""):
        return response.json()
    return response


def expect(client: TestClient, method: str, path: str, token: str, status: int, code: str, json=None):
    response = client.request(method, path, headers=auth(token), json=json)
    body = response.json() if response.content else {}
    assert response.status_code == status, body
    assert body.get("code") == code, body
    return body


def clear_cart(client: TestClient, token: str) -> None:
    cart = call(client, "GET", "/api/cart", token)
    for group in cart["groups"]:
        for line in group["lines"]:
            call(client, "DELETE", f"/api/cart/items/{line['id']}", token)
    if cart.get("coupon_code"):
        call(client, "DELETE", "/api/cart/coupon", token)


def available(client: TestClient, product_id: str, variant_id: str) -> int:
    detail = call(client, "GET", f"/api/store/products/{product_id}", None)
    return next(variant["available"] for variant in detail["variants"] if variant["id"] == variant_id)


@pytest.fixture(scope="session")
def database():
    assert settings.database_url.endswith("/bazaar_test"), settings.database_url
    owner = create_engine(settings.owner_database_url)
    with owner.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT USAGE ON SCHEMA public TO bazaar_app"))
    owner.dispose()
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.attributes["skip_logging"] = True
    command.upgrade(cfg, "head")
    reset_database()
    yield


@pytest.fixture(scope="session")
def client(database):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def tokens(client: TestClient) -> dict[str, str]:
    issued = {}
    for name, email in ACCOUNTS.items():
        response = client.post("/api/auth/token", data={"username": email, "password": "demo"})
        assert response.status_code == 200, response.text
        issued[name] = response.json()["access_token"]
    return issued


@pytest.fixture(scope="session")
def app_engine(database) -> Engine:
    engine = create_engine(settings.database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def as_app(app_engine: Engine):
    """Run SQL as bazaar_app inside one transaction with an RLS scope."""

    def run(scope: str, sql: str, *, user_id: str = "", vendor_id: str = "", **params):
        with app_engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT set_config('app.scope', :scope, true),"
                    " set_config('app.user_id', :user_id, true),"
                    " set_config('app.vendor_id', :vendor_id, true)"
                ),
                {"scope": scope, "user_id": user_id, "vendor_id": vendor_id},
            )
            rows = conn.execute(text(sql), params).all()
            conn.rollback()
            return rows

    return run


@pytest.fixture(autouse=True)
def no_unaudited_mutations():
    start = len(AUDIT_VIOLATIONS)
    yield
    fresh = AUDIT_VIOLATIONS[start:]
    assert not fresh, fresh
