import pytest

from app.schemas import VideoChoice, VideoCreate
from app.services import pipeline
from app.services.errors import PipelineError
from app.services.pipeline import BACKGROUND_FILES, build_narration, generate_short, resolve_background
from app.services.subtitles import Segment


def test_build_narration_matches_original_format():
    assert (
        build_narration("AITA", "Was I wrong?", "Long story.")
        == "From the subreddit AITA, Was I wrong?. Long story."
    )


def test_every_choice_has_a_background():
    assert set(BACKGROUND_FILES) == set(VideoChoice)


@pytest.mark.parametrize(
    "choice, file_name",
    [
        (VideoChoice.SUBWAY_SURFERS, "SubwaySurfers.mov"),
        (VideoChoice.MINECRAFT_PARKOR, "MinecraftParkor.mov"),
        (VideoChoice.MOBILE_GAME, "MobileGamplay.mov"),
    ],
)
def test_resolve_background(tmp_path, choice, file_name):
    (tmp_path / file_name).write_bytes(b"mov")
    assert resolve_background(choice, tmp_path) == tmp_path / file_name


@pytest.mark.parametrize("choice", list(VideoChoice))
def test_resolve_background_missing_file(tmp_path, choice):
    with pytest.raises(PipelineError, match=choice.value):
        resolve_background(choice, tmp_path)


def test_resolve_background_rejects_directory(tmp_path):
    (tmp_path / "SubwaySurfers.mov").mkdir()
    with pytest.raises(PipelineError):
        resolve_background(VideoChoice.SUBWAY_SURFERS, tmp_path)


@pytest.fixture
def video():
    return VideoCreate(
        subreddit="AITA",
        post_title="Title",
        content="Body",
        file_name="f",
        video_choice=VideoChoice.MINECRAFT_PARKOR,
    )


def test_generate_short_wires_pipeline(monkeypatch, tmp_path, settings, video):
    (settings.backgrounds_dir / "MinecraftParkor.mov").write_bytes(b"mov")
    segments = [Segment(0, 1, "x")]
    calls = {}

    def fake_subtitles(text, mp3_path, model_name):
        calls["subtitles"] = (text, mp3_path, model_name)
        return segments

    def fake_render(segs, background, audio, output, font):
        calls["render"] = (segs, background, audio, output, font)
        return output

    monkeypatch.setattr(pipeline, "create_subtitles", fake_subtitles)
    monkeypatch.setattr(pipeline, "render_video", fake_render)

    result = generate_short(video, tmp_path, settings)
    assert result == tmp_path / "short.mp4"
    assert calls["subtitles"] == ("From the subreddit AITA, Title. Body", tmp_path / "narration.mp3", "tiny")
    assert calls["render"] == (
        segments,
        settings.backgrounds_dir / "MinecraftParkor.mov",
        tmp_path / "narration.mp3",
        tmp_path / "short.mp4",
        "Futura-Bold",
    )


def test_generate_short_fails_fast_without_background(monkeypatch, tmp_path, settings, video):
    def should_not_run(*a, **k):
        raise AssertionError("TTS should not run when the background is missing")

    monkeypatch.setattr(pipeline, "create_subtitles", should_not_run)
    with pytest.raises(PipelineError, match="minecraftParkor"):
        generate_short(video, tmp_path, settings)


def test_generate_short_end_to_end_through_api(client, app, monkeypatch, settings, payload):
    """Use the real generate_short with only the heavy libraries stubbed."""
    from app.dependencies import get_video_generator

    app.dependency_overrides.pop(get_video_generator)
    (settings.backgrounds_dir / "SubwaySurfers.mov").write_bytes(b"mov")

    def fake_subtitles(text, mp3_path, model_name):
        mp3_path.write_bytes(b"mp3")
        return [Segment(0, 1, "x")]

    def fake_render(segs, background, audio, output, font):
        output.write_bytes(b"rendered")
        return output

    monkeypatch.setattr(pipeline, "create_subtitles", fake_subtitles)
    monkeypatch.setattr(pipeline, "render_video", fake_render)

    response = client.post("/shorts/create/", json=payload)
    assert response.status_code == 200
    assert response.content == b"rendered"


def test_missing_background_through_api_is_500(client, app, payload):
    from app.dependencies import get_video_generator

    app.dependency_overrides.pop(get_video_generator)
    response = client.post("/shorts/create/", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Background video for 'subwaySurfers' is missing"}
