import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from app.config import Settings, normalize_database_url
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


BACKEND_DIR = Path(__file__).resolve().parent.parent

# Any database on the test server works; each session creates and drops its own.
TEST_SERVER_URL = normalize_database_url(
    os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://shorts:shorts@localhost:5433/postgres")
)


def alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="session")
def database_url() -> str:
    """A fresh, migrated Postgres database for this test session."""
    admin = create_engine(TEST_SERVER_URL, isolation_level="AUTOCOMMIT")
    name = f"shorts_test_{uuid.uuid4().hex[:12]}"
    try:
        with admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    except OperationalError as exc:
        admin.dispose()
        pytest.fail(
            f"Can't reach Postgres at {make_url(TEST_SERVER_URL).render_as_string()}.\n"
            "Start it with `docker compose up -d` in backend/api, "
            "or point TEST_DATABASE_URL at another server.\n"
            f"{exc}",
            pytrace=False,
        )

    url = make_url(TEST_SERVER_URL).set(database=name).render_as_string(hide_password=False)
    command.upgrade(alembic_config(url), "head")
    yield url

    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture(scope="session")
def db_engine(database_url):
    engine = create_engine(database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def clean_db(db_engine):
    """Empty every table (and reset ids) so each test starts from scratch."""
    with db_engine.begin() as conn:
        conn.execute(text("TRUNCATE videos RESTART IDENTITY"))
    return db_engine


@pytest.fixture
def settings(tmp_path: Path, database_url: str, clean_db) -> Settings:
    backgrounds = tmp_path / "backgrounds"
    backgrounds.mkdir()
    return Settings(
        database_url=database_url,
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
