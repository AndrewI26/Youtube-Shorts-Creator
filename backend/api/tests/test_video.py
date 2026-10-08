import sys
from types import ModuleType

import pytest

from app.services.errors import PipelineError
from app.services.subtitles import Segment
from app.services.video import CAPTION_STYLE, render_video


class FakeClip:
    instances: list["FakeClip"] = []

    def __init__(self, *args, duration=10.0, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.duration = duration
        self.closed = False
        self.calls = []
        FakeClip.instances.append(self)

    def _record(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))
        return self

    def subclip(self, *a, **k):
        return self._record("subclip", *a, **k)

    def set_audio(self, *a, **k):
        return self._record("set_audio", *a, **k)

    def set_position(self, *a, **k):
        return self._record("set_position", *a, **k)

    def set_duration(self, *a, **k):
        return self._record("set_duration", *a, **k)

    def set_start(self, *a, **k):
        return self._record("set_start", *a, **k)

    def write_videofile(self, *a, **k):
        self._record("write_videofile", *a, **k)
        if FakeMoviepy.write_error:
            raise FakeMoviepy.write_error

    def close(self):
        self.closed = True


class FakeMoviepy:
    background_duration = 60.0
    audio_duration = 5.0
    write_error: Exception | None = None


class VideoFileClip(FakeClip):
    def __init__(self, path):
        super().__init__(path, duration=FakeMoviepy.background_duration)


class AudioFileClip(FakeClip):
    def __init__(self, path):
        super().__init__(path, duration=FakeMoviepy.audio_duration)


class TextClip(FakeClip):
    pass


class CompositeVideoClip(FakeClip):
    pass


@pytest.fixture(autouse=True)
def fake_moviepy(monkeypatch):
    FakeClip.instances = []
    FakeMoviepy.background_duration = 60.0
    FakeMoviepy.audio_duration = 5.0
    FakeMoviepy.write_error = None
    editor = ModuleType("moviepy.editor")
    for cls in (VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip):
        setattr(editor, cls.__name__, cls)
    package = ModuleType("moviepy")
    package.editor = editor
    monkeypatch.setitem(sys.modules, "moviepy", package)
    monkeypatch.setitem(sys.modules, "moviepy.editor", editor)


SEGMENTS = [Segment(0.0, 1.0, "hello"), Segment(1.01, 2.0, "world"), Segment(2.01, 4.5, "bye")]


def of_type(cls):
    return [c for c in FakeClip.instances if type(c) is cls]


def render(tmp_path, segments=SEGMENTS):
    return render_video(segments, tmp_path / "bg.mov", tmp_path / "a.mp3", tmp_path / "out.mp4")


def test_returns_output_path(tmp_path):
    assert render(tmp_path) == tmp_path / "out.mp4"


def test_loads_background_and_audio(tmp_path):
    render(tmp_path)
    assert of_type(VideoFileClip)[0].args == (str(tmp_path / "bg.mov"),)
    assert of_type(AudioFileClip)[0].args == (str(tmp_path / "a.mp3"),)


def test_background_trimmed_to_audio_length(tmp_path):
    render(tmp_path)
    background = of_type(VideoFileClip)[0]
    assert ("subclip", (0, 5.0), {}) in background.calls
    assert background.calls[1][0] == "set_audio"


def test_background_trimmed_to_last_subtitle_if_longer_than_audio(tmp_path):
    FakeMoviepy.audio_duration = 3.0
    render(tmp_path)
    assert ("subclip", (0, 4.5), {}) in of_type(VideoFileClip)[0].calls


def test_one_caption_per_segment_with_timing(tmp_path):
    render(tmp_path)
    captions = of_type(TextClip)
    assert [c.kwargs["txt"] for c in captions] == ["hello", "world", "bye"]
    for caption, segment in zip(captions, SEGMENTS):
        assert ("set_position", (("center", "center"),), {}) in caption.calls
        assert ("set_duration", (segment.end - segment.start,), {}) in caption.calls
        assert ("set_start", (segment.start,), {"change_end": True}) in caption.calls


def test_caption_style_matches_original(tmp_path):
    render(tmp_path)
    kwargs = of_type(TextClip)[0].kwargs
    assert {k: kwargs[k] for k in CAPTION_STYLE} == CAPTION_STYLE
    assert kwargs["font"] == "Futura-Bold"
    assert kwargs["fontsize"] == 90


def test_custom_font(tmp_path):
    render_video(SEGMENTS, tmp_path / "bg.mov", tmp_path / "a.mp3", tmp_path / "o.mp4", font="/f.ttc")
    assert all(c.kwargs["font"] == "/f.ttc" for c in of_type(TextClip))


def test_composite_layers_background_then_captions(tmp_path):
    render(tmp_path)
    (composite,) = of_type(CompositeVideoClip)
    layers = composite.args[0]
    assert layers[0] is of_type(VideoFileClip)[0]
    assert layers[1:] == of_type(TextClip)


def test_writes_mp4_with_aac_audio(tmp_path):
    render(tmp_path)
    (composite,) = of_type(CompositeVideoClip)
    name, args, kwargs = next(c for c in composite.calls if c[0] == "write_videofile")
    assert args == (str(tmp_path / "out.mp4"),)
    assert kwargs["fps"] == 30
    assert kwargs["audio_codec"] == "aac"
    assert kwargs["remove_temp"] is True
    assert kwargs["temp_audiofile"].startswith(str(tmp_path))


def test_all_clips_closed_on_success(tmp_path):
    render(tmp_path)
    assert FakeClip.instances and all(c.closed for c in FakeClip.instances)


def test_all_clips_closed_when_write_fails(tmp_path):
    FakeMoviepy.write_error = OSError("disk full")
    with pytest.raises(OSError):
        render(tmp_path)
    assert all(c.closed for c in FakeClip.instances)


def test_background_too_short_raises(tmp_path):
    FakeMoviepy.background_duration = 4.0
    with pytest.raises(PipelineError, match="Background video is 4.0s"):
        render(tmp_path)
    assert all(c.closed for c in FakeClip.instances)
    assert of_type(TextClip) == []


def test_background_exactly_long_enough_is_ok(tmp_path):
    FakeMoviepy.background_duration = 5.0
    render(tmp_path)


def test_empty_segments_raise_before_touching_moviepy(tmp_path, monkeypatch):
    monkeypatch.delitem(sys.modules, "moviepy.editor")
    with pytest.raises(PipelineError, match="without subtitles"):
        render(tmp_path, segments=[])


def test_custom_fps(tmp_path):
    render_video(SEGMENTS, tmp_path / "bg.mov", tmp_path / "a.mp3", tmp_path / "o.mp4", fps=24)
    (composite,) = of_type(CompositeVideoClip)
    assert composite.calls[-1][2]["fps"] == 24
