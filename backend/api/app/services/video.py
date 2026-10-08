from pathlib import Path
from typing import Sequence

from .errors import PipelineError
from .subtitles import Segment

CAPTION_STYLE = {
    "fontsize": 90,
    "size": (800, 0),
    "color": "white",
    "stroke_color": "black",
    "stroke_width": 5,
    "method": "caption",
}


def render_video(
    segments: Sequence[Segment],
    background_path: Path,
    audio_path: Path,
    output_path: Path,
    fps: int = 30,
    font: str = "Futura-Bold",
) -> Path:
    """Overlay captions and narration on the background gameplay clip."""
    if not segments:
        raise PipelineError("Cannot render a video without subtitles")

    from moviepy.editor import AudioFileClip, CompositeVideoClip, TextClip, VideoFileClip

    clips = []
    try:
        background = VideoFileClip(str(background_path))
        clips.append(background)
        audio = AudioFileClip(str(audio_path))
        clips.append(audio)

        duration = max(audio.duration, segments[-1].end)
        if background.duration < duration:
            raise PipelineError(
                f"Background video is {background.duration:.1f}s but narration needs {duration:.1f}s"
            )
        base = background.subclip(0, duration).set_audio(audio)

        txt_clips = []
        for segment in segments:
            txt_clip = (
                TextClip(txt=segment.text, font=font, **CAPTION_STYLE)
                .set_position(("center", "center"))
                .set_duration(segment.end - segment.start)
                .set_start(segment.start, change_end=True)
            )
            txt_clips.append(txt_clip)
            clips.append(txt_clip)

        video = CompositeVideoClip([base, *txt_clips])
        clips.append(video)
        video.write_videofile(
            str(output_path),
            fps=fps,
            temp_audiofile=str(output_path.with_name(output_path.stem + "-temp-audio.m4a")),
            remove_temp=True,
            audio_codec="aac",
            logger=None,
        )
    finally:
        for clip in reversed(clips):
            clip.close()

    return output_path
