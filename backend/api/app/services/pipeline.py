from pathlib import Path

from ..config import Settings
from ..schemas import VideoChoice, VideoCreate
from .errors import PipelineError
from .subtitles import create_subtitles
from .video import render_video

BACKGROUND_FILES = {
    VideoChoice.SUBWAY_SURFERS: "SubwaySurfers.mov",
    VideoChoice.MINECRAFT_PARKOR: "MinecraftParkor.mov",
    VideoChoice.MOBILE_GAME: "MobileGamplay.mov",
}


def build_narration(subreddit: str, post_title: str, content: str) -> str:
    return f"From the subreddit {subreddit}, {post_title}. {content}"


def resolve_background(choice: VideoChoice, backgrounds_dir: Path) -> Path:
    path = backgrounds_dir / BACKGROUND_FILES[choice]
    if not path.is_file():
        raise PipelineError(f"Background video for '{choice.value}' is missing")
    return path


def generate_short(video: VideoCreate, work_dir: Path, settings: Settings) -> Path:
    """Run the full narration -> subtitles -> render pipeline inside ``work_dir``."""
    background = resolve_background(video.video_choice, settings.backgrounds_dir)
    narration = build_narration(video.subreddit, video.post_title, video.content)
    audio_path = work_dir / "narration.mp3"
    segments = create_subtitles(narration, audio_path, settings.whisper_model)
    return render_video(
        segments, background, audio_path, work_dir / "short.mp4", font=settings.caption_font
    )
