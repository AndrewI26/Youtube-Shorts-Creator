import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol, Sequence

from .errors import PipelineError


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


class TimedText(Protocol):
    start: float
    end: float
    text: str


def split_segments(segments: Sequence[TimedText]) -> list[Segment]:
    """Split each transcribed segment in half so captions stay short on screen."""
    new_segments: list[Segment] = []
    for segment in segments:
        words = segment.text.split()
        if not words:
            continue
        if len(words) == 1:
            new_segments.append(Segment(segment.start, segment.end, words[0]))
            continue

        time_of_middle = round((segment.start + segment.end) / 2, 2)
        pos_middle = math.ceil(len(words) / 2)
        second_start = min(round(time_of_middle + 0.01, 2), segment.end)

        new_segments.append(Segment(segment.start, time_of_middle, " ".join(words[:pos_middle])))
        new_segments.append(Segment(second_start, segment.end, " ".join(words[pos_middle:])))

    return new_segments


def synthesize_speech(text: str, mp3_path: Path) -> Path:
    from gtts import gTTS

    gTTS(text, lang="en").save(str(mp3_path))
    return mp3_path


def extract_audio(mp3_path: Path) -> Path:
    import ffmpeg

    wav_path = mp3_path.with_suffix(".wav")
    stream = ffmpeg.output(ffmpeg.input(str(mp3_path)), str(wav_path))
    ffmpeg.run(stream, overwrite_output=True, quiet=True)
    return wav_path


@lru_cache(maxsize=2)
def _load_whisper_model(model_name: str):
    from faster_whisper import WhisperModel

    return WhisperModel(model_name)


def transcribe(audio_path: Path, model_name: str) -> list[Segment]:
    model = _load_whisper_model(model_name)
    segments, _info = model.transcribe(str(audio_path), chunk_length=10)
    return split_segments(list(segments))


def create_subtitles(text: str, mp3_path: Path, model_name: str) -> list[Segment]:
    """Narrate ``text`` to ``mp3_path`` and return timed caption segments."""
    synthesize_speech(text, mp3_path)
    wav_path = extract_audio(mp3_path)
    segments = transcribe(wav_path, model_name)
    if not segments:
        raise PipelineError("Transcription produced no subtitles")
    return segments
