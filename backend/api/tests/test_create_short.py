import pytest
from sqlalchemy import func, select

from app.models import Video
from app.services.errors import PipelineError

from .conftest import FAKE_MP4

REQUIRED_FIELDS = ["subreddit", "post_title", "content", "file_name", "video_choice"]


def row_count(app) -> int:
    with app.state.session_factory() as session:
        return session.scalar(select(func.count()).select_from(Video))


def media_entries(settings):
    return list(settings.media_dir.iterdir()) if settings.media_dir.exists() else []


# --- happy path --------------------------------------------------------------


def test_create_returns_video_file(client, payload):
    response = client.post("/shorts/create/", json=payload)
    assert response.status_code == 200
    assert response.content == FAKE_MP4
    assert response.headers["content-type"] == "video/mp4"
    assert 'filename="short.mp4"' in response.headers["content-disposition"]
    assert response.headers["content-disposition"].startswith("attachment")


def test_create_persists_request(client, app, payload):
    client.post("/shorts/create/", json=payload)
    with app.state.session_factory() as session:
        video = session.scalars(select(Video)).one()
    assert video.subreddit == "AITA"
    assert video.post_title == payload["post_title"]
    assert video.content == payload["content"]
    assert video.file_name == "I (25F)"  # surrounding whitespace stripped
    assert video.video_choice == "subwaySurfers"


def test_create_passes_validated_request_to_generator(client, generator, payload):
    client.post("/shorts/create/", json=payload)
    assert len(generator.calls) == 1
    video, _ = generator.calls[0]
    assert video.subreddit == "AITA"
    assert video.video_choice.value == "subwaySurfers"


@pytest.mark.parametrize("choice", ["subwaySurfers", "minecraftParkor", "mobileGame"])
def test_create_accepts_every_video_choice(client, generator, payload, choice):
    response = client.post("/shorts/create/", json={**payload, "video_choice": choice})
    assert response.status_code == 200
    assert generator.calls[0][0].video_choice.value == choice


def test_create_accepts_urlencoded_form(client, generator, payload):
    response = client.post("/shorts/create/", data=payload)
    assert response.status_code == 200
    assert response.content == FAKE_MP4
    assert generator.calls[0][0].post_title == payload["post_title"]


def test_create_accepts_multipart_form_like_sample_curl(client, generator, payload):
    # backend/sample.txt posts with `curl -F`, including an extra video_file field.
    files = {key: (None, value) for key, value in payload.items()}
    files["video_file"] = (None, "/some/local/path.mp4")
    response = client.post("/shorts/create/", files=files)
    assert response.status_code == 200
    assert generator.calls[0][0].subreddit == "AITA"


def test_create_without_trailing_slash_redirects_and_succeeds(client, payload):
    response = client.post("/shorts/create", json=payload)
    assert response.status_code == 200
    assert response.content == FAKE_MP4


def test_create_ignores_unknown_fields(client, payload):
    response = client.post("/shorts/create/", json={**payload, "id": 999, "extra": "x"})
    assert response.status_code == 200


def test_create_handles_unicode_text(client, generator, payload):
    payload = {**payload, "post_title": "Café drama 😬", "content": "Ünïcödé — “quotes”"}
    response = client.post("/shorts/create/", json=payload)
    assert response.status_code == 200
    assert generator.calls[0][0].content == "Ünïcödé — “quotes”"


def test_create_accepts_long_content(client, payload):
    response = client.post("/shorts/create/", json={**payload, "content": "word " * 5000})
    assert response.status_code == 200


def test_each_request_gets_its_own_work_dir(client, generator, payload):
    client.post("/shorts/create/", json=payload)
    client.post("/shorts/create/", json=payload)
    first, second = generator.calls[0][1], generator.calls[1][1]
    assert first != second
    assert first.parent == second.parent


def test_work_dir_is_removed_after_response(client, settings, generator, payload):
    client.post("/shorts/create/", json=payload)
    work_dir = generator.calls[0][1]
    assert not work_dir.exists()
    assert media_entries(settings) == []


def test_work_dir_name_is_sanitized(client, generator, payload):
    client.post("/shorts/create/", json={**payload, "file_name": "my/../weird name!"})
    work_dir = generator.calls[0][1]
    assert work_dir.name.startswith("my-weird-name-")


@pytest.mark.parametrize("file_name", ["../../etc/passwd", "/abs/path", "..", "a\\b\\..\\c", "~"])
def test_file_name_cannot_escape_media_dir(client, settings, generator, payload, file_name):
    response = client.post("/shorts/create/", json={**payload, "file_name": file_name})
    assert response.status_code == 200
    work_dir = generator.calls[0][1]
    assert work_dir.parent == settings.media_dir


def test_multiple_creates_accumulate_rows(client, app, payload):
    for i in range(5):
        client.post("/shorts/create/", json={**payload, "file_name": f"clip {i}"})
    assert row_count(app) == 5


# --- validation --------------------------------------------------------------


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_missing_field_is_422(client, app, generator, payload, field):
    del payload[field]
    response = client.post("/shorts/create/", json=payload)
    assert response.status_code == 422
    locs = [error["loc"] for error in response.json()["detail"]]
    assert [field] in locs
    assert generator.calls == []
    assert row_count(app) == 0


@pytest.mark.parametrize("field", ["subreddit", "post_title", "content", "file_name"])
@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_blank_text_field_is_422(client, app, generator, payload, field, blank):
    response = client.post("/shorts/create/", json={**payload, field: blank})
    assert response.status_code == 422
    assert generator.calls == []
    assert row_count(app) == 0


@pytest.mark.parametrize("choice", ["", "subway", "SubwaySurfers", "minecraftParkour", "tiktok", None])
def test_invalid_video_choice_is_422(client, generator, payload, choice):
    response = client.post("/shorts/create/", json={**payload, "video_choice": choice})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["video_choice"]
    assert generator.calls == []


@pytest.mark.parametrize("field", ["subreddit", "post_title", "content", "file_name"])
@pytest.mark.parametrize("value", [123, 1.5, True, ["a"], {"a": 1}, None])
def test_non_string_field_is_422(client, generator, payload, field, value):
    response = client.post("/shorts/create/", json={**payload, field: value})
    assert response.status_code == 422
    assert generator.calls == []


def test_subreddit_too_long_is_422(client, payload):
    response = client.post("/shorts/create/", json={**payload, "subreddit": "a" * 256})
    assert response.status_code == 422


def test_subreddit_at_max_length_is_ok(client, payload):
    response = client.post("/shorts/create/", json={**payload, "subreddit": "a" * 255})
    assert response.status_code == 200


def test_file_name_too_long_is_422(client, payload):
    response = client.post("/shorts/create/", json={**payload, "file_name": "a" * 226})
    assert response.status_code == 422


def test_invalid_json_is_422(client, app, generator):
    response = client.post(
        "/shorts/create/", content=b"{not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"
    assert generator.calls == []
    assert row_count(app) == 0


def test_non_utf8_body_is_422(client):
    response = client.post(
        "/shorts/create/", content=b"\xff\xfe\xfa", headers={"content-type": "application/json"}
    )
    assert response.status_code == 422


def test_empty_body_is_422(client):
    response = client.post("/shorts/create/")
    assert response.status_code == 422


@pytest.mark.parametrize("body", ["[]", '"string"', "42", "null", "[{}]"])
def test_non_object_json_is_422(client, generator, body):
    response = client.post(
        "/shorts/create/", content=body, headers={"content-type": "application/json"}
    )
    assert response.status_code == 422
    assert generator.calls == []


def test_empty_form_is_422(client):
    response = client.post("/shorts/create/", data={"unrelated": "x"})
    assert response.status_code == 422
    assert len(response.json()["detail"]) == len(REQUIRED_FIELDS)


def test_uploaded_file_in_text_field_is_422(client, payload):
    data = {k: v for k, v in payload.items() if k != "content"}
    response = client.post(
        "/shorts/create/", data=data, files={"content": ("c.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 422


def test_get_on_create_is_405(client):
    assert client.get("/shorts/create/").status_code == 405


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_other_methods_on_create_are_405(client, method):
    assert getattr(client, method)("/shorts/create/").status_code == 405


# --- generation failures ------------------------------------------------------


def test_pipeline_error_returns_500_with_message(client, generator, payload):
    generator.error = PipelineError("Background video for 'subwaySurfers' is missing")
    response = client.post("/shorts/create/", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Background video for 'subwaySurfers' is missing"}


def test_unexpected_error_returns_generic_500(client, generator, payload, caplog):
    generator.error = RuntimeError("secret internal path /Users/x")
    response = client.post("/shorts/create/", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Video generation failed"}
    assert "secret" not in response.text
    assert "Video generation failed" in caplog.text


def test_missing_output_returns_500(client, generator, payload):
    generator.write_output = False
    response = client.post("/shorts/create/", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Video generation produced no file"}


@pytest.mark.parametrize("error", [PipelineError("x"), RuntimeError("y"), None])
def test_work_dir_is_cleaned_up_on_failure(client, settings, generator, payload, error):
    if error is None:
        generator.write_output = False
    else:
        generator.error = error
    client.post("/shorts/create/", json=payload)
    assert not generator.calls[0][1].exists()
    assert media_entries(settings) == []


def test_request_is_recorded_even_if_generation_fails(client, app, generator, payload):
    # Matches the old Django view, which saved the row before rendering.
    generator.error = PipelineError("boom")
    client.post("/shorts/create/", json=payload)
    assert row_count(app) == 1


def test_app_recovers_after_a_failure(client, generator, payload):
    generator.error = PipelineError("boom")
    assert client.post("/shorts/create/", json=payload).status_code == 500
    generator.error = None
    assert client.post("/shorts/create/", json=payload).status_code == 200
