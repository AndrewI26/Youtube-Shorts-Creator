from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_video_generator
from app.main import create_app
from app.schemas import VideoCreate

FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42fake-video-bytes"


class FakeGenerator:
    """Stands in for the real TTS/whisper/moviepy pipeline."""

    def __init__(self):
        self.calls: list[tuple[VideoCreate, Path]] = []
        self.error: Exception | None = None
        self.write_output = True

    def __call__(self, video: VideoCreate, work_dir: Path) -> Path:
        self.calls.append((video, work_dir))
        assert work_dir.is_dir()
        if self.error:
            # Leave partial artifacts behind to prove the route cleans them up.
            (work_dir / "narration.mp3").write_bytes(b"partial")
            raise self.error
        output = work_dir / "short.mp4"
        if self.write_output:
            output.write_bytes(FAKE_MP4)
        return output


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    backgrounds = tmp_path / "backgrounds"
    backgrounds.mkdir()
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.sqlite3'}",
        media_dir=tmp_path / "media",
        backgrounds_dir=backgrounds,
        whisper_model="tiny",
        cors_origins=["*"],
    )


@pytest.fixture
def generator() -> FakeGenerator:
    return FakeGenerator()


@pytest.fixture
def app(settings: Settings, generator: FakeGenerator):
    app = create_app(settings)
    app.dependency_overrides[get_video_generator] = lambda: generator
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def payload() -> dict[str, str]:
    return {
        "subreddit": "AITA",
        "post_title": "AITA for leaving the party early?",
        "content": "I (25F) left my friend's party after an hour.",
        "file_name": "I (25F) ",
        "video_choice": "subwaySurfers",
    }
