from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    environment: str = "development"

    database_url: str = "postgresql+psycopg://bazaar_app:bazaar_app@127.0.0.1:5432/bazaar"
    owner_database_url: str = "postgresql+psycopg://bazaar_owner:bazaar_owner@127.0.0.1:5432/bazaar"
    test_database_url: str = "postgresql+psycopg://bazaar_app:bazaar_app@127.0.0.1:5432/bazaar_test"
    test_owner_database_url: str = (
        "postgresql+psycopg://bazaar_owner:bazaar_owner@127.0.0.1:5432/bazaar_test"
    )
    app_db_role: str = "bazaar_app"

    jwt_secret: str = "dev-only-secret-change-me-before-any-real-deployment"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cookie_name: str = "bazaar_session"
    cookie_secure: bool = False

    holdback_days: int = 7
    reservation_minutes: int = 15
    max_upload_bytes: int = 5 * 1024 * 1024

    login_rate_limit: int = 10
    login_rate_window_seconds: int = 300

    # When true, a successful mutating request that wrote no audit row is recorded
    # as a violation (the test suite fails on any violation).
    strict_audit: bool = False
    # Background maintenance loop is a poor fit for serverless; keep off on Vercel.
    run_maintenance: bool = True

    media_dir: Path = BACKEND_DIR / "media"
    private_dir: Path = BACKEND_DIR / "private"

    # Mail — always written to private/mailbox. Set SMTP_* to also deliver.
    mail_from: str = "Bazaar <noreply@bazaar.local>"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    otp_ttl_minutes: int = 15
    # When true (default in development), register/verify responses include the OTP for demos.
    expose_otp_in_api: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
