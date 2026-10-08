import pytest
from pydantic import ValidationError

from app.models import Video
from app.schemas import VideoChoice, VideoCreate, VideoRead

VALID = {
    "subreddit": "AITA",
    "post_title": "Title",
    "content": "Body",
    "file_name": "file",
    "video_choice": "mobileGame",
}


def test_video_choice_values_match_frontend_options():
    assert {c.value for c in VideoChoice} == {"subwaySurfers", "minecraftParkor", "mobileGame"}


def test_video_create_parses_enum():
    video = VideoCreate.model_validate(VALID)
    assert video.video_choice is VideoChoice.MOBILE_GAME


def test_video_create_strips_whitespace():
    video = VideoCreate.model_validate({**VALID, "subreddit": "  AITA  ", "content": "\n Body \n"})
    assert video.subreddit == "AITA"
    assert video.content == "Body"


def test_video_create_dumps_enum_as_string():
    assert VideoCreate.model_validate(VALID).model_dump(mode="json")["video_choice"] == "mobileGame"


def test_video_create_reports_all_errors_at_once():
    with pytest.raises(ValidationError) as exc:
        VideoCreate.model_validate({})
    assert {e["loc"][0] for e in exc.value.errors()} == set(VALID)


@pytest.mark.parametrize("field, max_len", [("subreddit", 255), ("file_name", 225)])
def test_video_create_length_limits(field, max_len):
    VideoCreate.model_validate({**VALID, field: "x" * max_len})
    with pytest.raises(ValidationError):
        VideoCreate.model_validate({**VALID, field: "x" * (max_len + 1)})


def test_video_create_rejects_numbers_for_strings():
    with pytest.raises(ValidationError):
        VideoCreate.model_validate({**VALID, "file_name": 12})


def test_video_read_from_orm():
    video = Video(id=7, **{**VALID, "video_choice": "legacy"})
    read = VideoRead.model_validate(video)
    assert read.id == 7
    assert read.video_choice == "legacy"
