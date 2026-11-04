"""Flask-based HTTP layer with FastAPI-compatible router signatures."""

from app.flaskapi.params import Depends, File, Form, Query
from app.flaskapi.request import Request
from app.flaskapi.response import FileResponse, Response
from app.flaskapi.routing import APIRouter, UploadFile
from app.flaskapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.flaskapi.testing import TestClient

__all__ = [
    "APIRouter",
    "Depends",
    "File",
    "FileResponse",
    "Form",
    "OAuth2PasswordBearer",
    "OAuth2PasswordRequestForm",
    "Query",
    "Request",
    "Response",
    "TestClient",
    "UploadFile",
]
