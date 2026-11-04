"""Vercel Flask entrypoint (re-exports the application)."""

from app.main import app

__all__ = ["app"]
