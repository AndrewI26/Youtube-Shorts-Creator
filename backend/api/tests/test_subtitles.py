import sys
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace

import pytest

from app.services import subtitles
from app.services.errors import PipelineError
from app.services.subtitles import Segment, split_segments


@dataclass
class Raw:
    start: float
    end: float
    text: str


# --- split_segments -----------------------------------------------------------


def test_split_even_word_count():
    assert split_segments([Raw(0.0, 2.0, "one two three four")]) == [
        Segment(0.0, 1.0, "one two"),
        Segment(1.01, 2.0, "three four"),
    ]


def test_split_odd_word_count_puts_extra_word_first():
    assert split_segments([Raw(0.0, 3.0, "a b c")]) == [
        Segment(0.0, 1.5, "a b"),
        Segment(1.51, 3.0, "c"),
    ]


def test_split_two_words():
    assert split_segments([Raw(1.0, 2.0, "hello world")]) == [
        Segment(1.0, 1.5, "hello"),
        Segment(1.51, 2.0, "world"),
    ]


def test_single_word_segment_is_not_split():
    assert split_segments([Raw(0.5, 0.9, " Hi ")]) == [Segment(0.5, 0.9, "Hi")]


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_segments_are_dropped(text):
    assert split_segments([Raw(0.0, 1.0, text)]) == []


def test_empty_input():
    assert split_segments([]) == []


def test_middle_time_is_rounded():
    first, second = split_segments([Raw(0.0, 1.333, "a b")])
    assert first.end == 0.67
    assert second.start == 0.68


def test_second_half_never_starts_after_segment_end():
    first, second = split_segments([Raw(1.0, 1.005, "a b")])
    assert second.start <= second.end
    assert first.start <= first.end


def test_extra_whitespace_is_normalised():
    first, second = split_segments([Raw(0, 2, "  lots   of\tspace  here ")])
    assert first.text == "lots of"
    assert second.text == "space here"


def test_multiple_segments_preserve_order_and_count():
    raw = [Raw(0, 1, "a b"), Raw(1, 2, "c"), Raw(2, 3, ""), Raw(3, 4, "d e f g")]
    result = split_segments(raw)
    assert [s.text for s in result] == ["a", "b", "c", "d e", "f g"]
    starts = [s.start for s in result]
    assert starts == sorted(starts)


def test_all_words_are_kept():
    text = "the quick brown fox jumps over the lazy dog"
    result = split_segments([Raw(0, 5, text)])
    assert " ".join(s.text for s in result) == text


def test_accepts_any_object_with_start_end_text():
    raw = SimpleNamespace(start=0, end=2, text="x y")
    assert len(split_segments([raw])) == 2


def test_segment_is_immutable():
    with pytest.raises(Exception):
        Segment(0, 1, "a").text = "b"


# --- synthesize / extract / transcribe -----------------------------------------


def test_synthesize_speech_uses_gtts(monkeypatch, tmp_path):
    saved = {}

    class FakeTTS:
        def __init__(self, text, lang):
            saved["args"] = (text, lang)

        def save(self, path):
            saved["path"] = path

    module = ModuleType("gtts")
    module.gTTS = FakeTTS
    monkeypatch.setitem(sys.modules, "gtts", module)

    out = subtitles.synthesize_speech("hello", tmp_path / "a.mp3")
    assert out == tmp_path / "a.mp3"
    assert saved == {"args": ("hello", "en"), "path": str(tmp_path / "a.mp3")}


def test_extract_audio_uses_ffmpeg(monkeypatch, tmp_path):
    calls = []
    module = ModuleType("ffmpeg")
    module.input = lambda path: ("input", path)
    module.output = lambda stream, path: ("output", stream, path)
    module.run = lambda stream, **kwargs: calls.append((stream, kwargs))
    monkeypatch.setitem(sys.modules, "ffmpeg", module)

    wav = subtitles.extract_audio(tmp_path / "narration.mp3")
    assert wav == tmp_path / "narration.wav"
    stream, kwargs = calls[0]
    assert stream == ("output", ("input", str(tmp_path / "narration.mp3")), str(wav))
    assert kwargs["overwrite_output"] is True


@pytest.fixture
def fake_whisper(monkeypatch):
    created = []

    class FakeModel:
        def __init__(self, name):
            self.name = name
            self.transcribed = []
            created.append(self)

        def transcribe(self, path, chunk_length):
            self.transcribed.append((path, chunk_length))
            return iter([Raw(0, 1, "hello there"), Raw(1, 2, "friend")]), SimpleNamespace(language="en")

    module = ModuleType("faster_whisper")
    module.WhisperModel = FakeModel
    monkeypatch.setitem(sys.modules, "faster_whisper", module)
    subtitles._load_whisper_model.cache_clear()
    yield created
    subtitles._load_whisper_model.cache_clear()


def test_transcribe_splits_whisper_segments(fake_whisper, tmp_path):
    result = subtitles.transcribe(tmp_path / "a.wav", "tiny")
    assert result == [Segment(0, 0.5, "hello"), Segment(0.51, 1, "there"), Segment(1, 2, "friend")]
    assert fake_whisper[0].name == "tiny"
    assert fake_whisper[0].transcribed == [(str(tmp_path / "a.wav"), 10)]


def test_whisper_model_is_cached_per_name(fake_whisper, tmp_path):
    subtitles.transcribe(tmp_path / "a.wav", "tiny")
    subtitles.transcribe(tmp_path / "b.wav", "tiny")
    assert len(fake_whisper) == 1
    subtitles.transcribe(tmp_path / "c.wav", "small")
    assert [m.name for m in fake_whisper] == ["tiny", "small"]


# --- create_subtitles ------------------------------------------------------------


def test_create_subtitles_runs_steps_in_order(monkeypatch, tmp_path):
    order = []
    mp3 = tmp_path / "n.mp3"
    monkeypatch.setattr(subtitles, "synthesize_speech", lambda text, path: order.append(("tts", text, path)))
    monkeypatch.setattr(
        subtitles, "extract_audio", lambda path: order.append(("extract", path)) or path.with_suffix(".wav")
    )
    monkeypatch.setattr(
        subtitles,
        "transcribe",
        lambda path, model: order.append(("transcribe", path, model)) or [Segment(0, 1, "x")],
    )

    result = subtitles.create_subtitles("text", mp3, "tiny")
    assert result == [Segment(0, 1, "x")]
    assert order == [
        ("tts", "text", mp3),
        ("extract", mp3),
        ("transcribe", tmp_path / "n.wav", "tiny"),
    ]


def test_create_subtitles_raises_when_nothing_transcribed(monkeypatch, tmp_path):
    monkeypatch.setattr(subtitles, "synthesize_speech", lambda *a: None)
    monkeypatch.setattr(subtitles, "extract_audio", lambda p: p)
    monkeypatch.setattr(subtitles, "transcribe", lambda *a: [])
    with pytest.raises(PipelineError, match="no subtitles"):
        subtitles.create_subtitles("text", tmp_path / "n.mp3", "tiny")


def test_create_subtitles_propagates_tts_errors(monkeypatch, tmp_path):
    def boom(*a):
        raise ConnectionError("gTTS offline")

    monkeypatch.setattr(subtitles, "synthesize_speech", boom)
    with pytest.raises(ConnectionError):
        subtitles.create_subtitles("text", tmp_path / "n.mp3", "tiny")
