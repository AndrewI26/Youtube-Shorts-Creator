import json
import re
import shutil
import uuid
from collections.abc import Callable
from functools import partial
from pathlib import Path

from fastapi import Depends, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from .config import Settings
from .schemas import VideoCreate
from .services.pipeline import generate_short

FORM_CONTENT_TYPES = ("multipart/form-data", "application/x-www-form-urlencoded")

VideoGenerator = Callable[[VideoCreate, Path], Path]


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_video_generator(settings: Settings = Depends(get_settings)) -> VideoGenerator:
    return partial(generate_short, settings=settings)


def _body_error(error_type: str, msg: str) -> RequestValidationError:
    return RequestValidationError([{"type": error_type, "loc": ("body",), "msg": msg, "input": None}])


async def parse_video_payload(request: Request) -> VideoCreate:
    """Accept JSON (the frontend) or form data (curl -F), like the old DRF view did."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith(FORM_CONTENT_TYPES):
        data = dict(await request.form())
    else:
        try:
            data = await request.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise _body_error("json_invalid", "Request body must be valid JSON")
    if not isinstance(data, dict):
        raise _body_error("model_attributes_type", "Request body must be an object")
    try:
        return VideoCreate.model_validate(data)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors(include_url=False))


def safe_stem(name: str, max_length: int = 50) -> str:
    """Turn a user-supplied file name into something safe to use in a path."""
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-_")
    return stem[:max_length].strip("-_") or "short"


def make_work_dir(media_dir: Path, file_name: str) -> Path:
    work_dir = media_dir / f"{safe_stem(file_name)}-{uuid.uuid4().hex[:12]}"
    work_dir.mkdir(parents=True)
    return work_dir


def remove_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
