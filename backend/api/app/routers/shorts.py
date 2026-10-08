import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from ..config import Settings
from ..database import get_db
from ..dependencies import (
    VideoGenerator,
    get_settings,
    get_video_generator,
    make_work_dir,
    parse_video_payload,
    remove_dir,
)
from ..models import Video
from ..schemas import VideoCreate, VideoRead
from ..services.errors import PipelineError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shorts", tags=["shorts"])


@router.get("/")
def api_overview() -> dict[str, str]:
    return {
        "Overview": "/shorts/",
        "All videos": "/shorts/all/",
        "Create": "/shorts/create/",
    }


@router.post(
    "/create/",
    response_class=FileResponse,
    responses={200: {"content": {"video/mp4": {}}, "description": "The generated short"}},
)
def create_short(
    video: VideoCreate = Depends(parse_video_payload),
    db: Session = Depends(get_db),
    generate: VideoGenerator = Depends(get_video_generator),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    db.add(Video(**video.model_dump(mode="json")))
    db.commit()

    work_dir = make_work_dir(settings.media_dir, video.file_name)
    try:
        output = generate(video, work_dir)
    except PipelineError as exc:
        remove_dir(work_dir)
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception:
        logger.exception("Video generation failed")
        remove_dir(work_dir)
        raise HTTPException(status_code=500, detail="Video generation failed")

    if not output.is_file():
        remove_dir(work_dir)
        raise HTTPException(status_code=500, detail="Video generation produced no file")

    return FileResponse(
        output,
        media_type="video/mp4",
        filename="short.mp4",
        background=BackgroundTask(remove_dir, work_dir),
    )


@router.get("/all/", response_model=list[VideoRead])
def view_videos(db: Session = Depends(get_db)) -> list[Video]:
    return list(db.scalars(select(Video).order_by(Video.id)))
