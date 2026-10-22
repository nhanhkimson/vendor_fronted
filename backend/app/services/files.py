"""Uploads: public product and shop images, private identity documents."""

import secrets
from pathlib import Path

from fastapi import UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.errors import NotFound, Unprocessable

IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
DOCUMENT_TYPES = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
MAGIC = {
    "jpg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "webp": (b"RIFF",),
    "pdf": (b"%PDF",),
}


def _read(upload: UploadFile, allowed: dict[str, str]) -> tuple[bytes, str]:
    content_type = (upload.content_type or "").lower()
    ext = allowed.get(content_type)
    if ext is None:
        raise Unprocessable(
            f"{upload.filename or 'File'} is {content_type or 'an unknown type'}. "
            f"Allowed: {', '.join(sorted(set(allowed.values())))}",
            code="file_type",
        )
    data = upload.file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise Unprocessable(
            f"{upload.filename or 'File'} is larger than {settings.max_upload_bytes // (1024 * 1024)} MB",
            code="file_too_large",
        )
    if not data:
        raise Unprocessable("The file is empty", code="file_empty")
    if not any(data.startswith(m) for m in MAGIC[ext]):
        raise Unprocessable("The file content does not match its type", code="file_type")
    return data, ext


def save_image(upload: UploadFile, folder: str, stem: str) -> str:
    data, ext = _read(upload, IMAGE_TYPES)
    name = f"{stem}-{secrets.token_hex(4)}.{ext}"
    target = settings.media_dir / "uploads" / folder / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return f"/media/uploads/{folder}/{name}"


def save_document(upload: UploadFile, vendor_id: str, doc_id: str) -> tuple[str, str]:
    data, ext = _read(upload, DOCUMENT_TYPES)
    relative = f"documents/{vendor_id}/{doc_id}-{secrets.token_hex(4)}.{ext}"
    target = settings.private_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return relative, upload.content_type or "application/octet-stream"


def document_response(relative: str | None, content_type: str | None, filename: str | None) -> FileResponse:
    if not relative:
        raise NotFound("Document file")
    path = (settings.private_dir / relative).resolve()
    root = settings.private_dir.resolve()
    if root not in path.parents or not Path(path).is_file():
        raise NotFound("Document file")
    return FileResponse(
        path,
        media_type=content_type or "application/octet-stream",
        filename=filename or path.name,
        content_disposition_type="inline",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
