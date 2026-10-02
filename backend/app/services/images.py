"""Validation and storage for images students attach to tutor messages."""
import base64
import uuid
from pathlib import Path

from app.config import settings

ALLOWED = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
UNSUPPORTED_MSG = "Unsupported file. Please upload a JPG, PNG or WEBP image."


class ImageError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message, self.status_code = message, status_code


def max_bytes() -> int:
    return int(settings.max_image_mb * 1024 * 1024)


def sniff_mime(data: bytes) -> str | None:
    """Detect the real type from the file's first bytes (the browser-supplied type is not trusted)."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate(data: bytes) -> str:
    """Returns the verified mime type or raises ImageError with a student-friendly message."""
    if not data:
        raise ImageError("The image file is empty. Please choose another one.")
    if len(data) > max_bytes():
        raise ImageError(f"That image is too large. The limit is {settings.max_image_mb:g} MB.", 413)
    mime = sniff_mime(data)
    if not mime:
        raise ImageError(UNSUPPORTED_MSG, 415)
    return mime


def root() -> Path:
    return Path(settings.upload_dir).resolve()


def save(user_id: int, data: bytes, mime: str) -> str:
    """Writes the image and returns its path relative to the upload root."""
    rel = Path("tutor") / str(user_id) / f"{uuid.uuid4().hex}.{ALLOWED[mime]}"
    dest = root() / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return rel.as_posix()


def resolve(rel: str) -> Path | None:
    """Absolute path for a stored image, or None if it escapes the upload root."""
    path = (root() / rel).resolve()
    return path if path.is_relative_to(root()) else None


def delete(rel: str | None) -> None:
    if not rel:
        return
    path = resolve(rel)
    try:
        if path and path.is_file():
            path.unlink()
    except OSError:
        pass  # best effort


def to_data_url(data: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
