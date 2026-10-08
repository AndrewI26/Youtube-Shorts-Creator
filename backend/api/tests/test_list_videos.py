import shutil
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.models import Video

LEGACY_DB = Path(__file__).resolve().parent.parent / "db.sqlite3"


def test_all_is_empty_list_when_no_videos(client):
    response = client.get("/shorts/all/")
    assert response.status_code == 200
    assert response.json() == []


def test_all_returns_created_videos_in_order(client, payload):
    for name in ["first", "second", "third"]:
        client.post("/shorts/create/", json={**payload, "file_name": name})
    videos = client.get("/shorts/all/").json()
    assert [v["file_name"] for v in videos] == ["first", "second", "third"]
    assert [v["id"] for v in videos] == [1, 2, 3]


def test_all_returns_every_field(client, payload):
    client.post("/shorts/create/", json=payload)
    (video,) = client.get("/shorts/all/").json()
    assert video == {
        "id": 1,
        "subreddit": payload["subreddit"],
        "post_title": payload["post_title"],
        "content": payload["content"],
        "file_name": payload["file_name"].strip(),
        "video_choice": payload["video_choice"],
    }


def test_all_includes_rows_from_failed_generations(client, generator, payload):
    generator.error = RuntimeError("boom")
    client.post("/shorts/create/", json=payload)
    assert len(client.get("/shorts/all/").json()) == 1


def test_all_does_not_include_invalid_requests(client, payload):
    client.post("/shorts/create/", json={**payload, "video_choice": "bogus"})
    assert client.get("/shorts/all/").json() == []


def test_all_returns_rows_with_unexpected_values(client, app):
    # Rows written by older code are returned verbatim rather than 500ing.
    with app.state.session_factory() as session:
        session.add(Video(subreddit="", post_title="", content="", file_name="", video_choice="old"))
        session.commit()
    response = client.get("/shorts/all/")
    assert response.status_code == 200
    assert response.json()[0]["video_choice"] == "old"


def test_post_on_all_is_405(client):
    assert client.post("/shorts/all/").status_code == 405


def test_data_persists_across_app_restarts(settings, generator, payload):
    from app.dependencies import get_video_generator

    for _ in range(2):
        app = create_app(settings)
        app.dependency_overrides[get_video_generator] = lambda: generator
        with TestClient(app) as client:
            client.post("/shorts/create/", json=payload)
    app = create_app(settings)
    with TestClient(app) as client:
        assert len(client.get("/shorts/all/").json()) == 2


def make_django_db(path: Path) -> None:
    """Recreate the exact table Django's migrations produced."""
    conn = sqlite3.connect(path)
    conn.execute(
        'CREATE TABLE "shorts_video" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, '
        '"subreddit" varchar(255) NOT NULL, "post_title" text NOT NULL, "content" text NOT NULL, '
        '"file_name" varchar(225) NOT NULL, "video_choice" varchar(500) NOT NULL)'
    )
    conn.execute(
        "INSERT INTO shorts_video (subreddit, post_title, content, file_name, video_choice) "
        "VALUES ('AITA', 'Old post', 'Old body', 'old', 'minecraftParkor')"
    )
    conn.commit()
    conn.close()


def test_reads_and_extends_django_schema(tmp_path, settings, generator, payload):
    from app.dependencies import get_video_generator

    db_path = tmp_path / "django.sqlite3"
    make_django_db(db_path)
    app = create_app(Settings(**{**settings.__dict__, "database_url": f"sqlite:///{db_path}"}))
    app.dependency_overrides[get_video_generator] = lambda: generator
    with TestClient(app) as client:
        videos = client.get("/shorts/all/").json()
        assert videos == [
            {
                "id": 1,
                "subreddit": "AITA",
                "post_title": "Old post",
                "content": "Old body",
                "file_name": "old",
                "video_choice": "minecraftParkor",
            }
        ]
        client.post("/shorts/create/", json=payload)
        assert [v["id"] for v in client.get("/shorts/all/").json()] == [1, 2]


@pytest.mark.skipif(not LEGACY_DB.exists(), reason="legacy db.sqlite3 not present")
def test_reads_existing_repo_database(tmp_path, settings):
    db_copy = tmp_path / "legacy.sqlite3"
    shutil.copy(LEGACY_DB, db_copy)
    with sqlite3.connect(db_copy) as conn:
        expected = conn.execute("SELECT COUNT(*) FROM shorts_video").fetchone()[0]
    app = create_app(Settings(**{**settings.__dict__, "database_url": f"sqlite:///{db_copy}"}))
    with TestClient(app) as client:
        response = client.get("/shorts/all/")
    assert response.status_code == 200
    assert len(response.json()) == expected
