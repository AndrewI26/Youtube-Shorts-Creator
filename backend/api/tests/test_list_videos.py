from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import Video


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


def test_round_trips_unicode_and_long_text(client, payload):
    content = "Ünïcödé 😬 “quotes” — " + "word " * 20_000
    client.post("/shorts/create/", json={**payload, "post_title": "Café ☕", "content": content})
    (video,) = client.get("/shorts/all/").json()
    assert video["post_title"] == "Café ☕"
    assert video["content"] == content.strip()


def test_concurrent_creates_get_unique_ids(client, payload):
    def create(i):
        return client.post("/shorts/create/", json={**payload, "file_name": f"clip {i}"}).status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert set(pool.map(create, range(16))) == {200}

    ids = [v["id"] for v in client.get("/shorts/all/").json()]
    assert sorted(ids) == list(range(1, 17))
