# python3 createSubtitles.py
from gtts import gTTS
from faster_whisper import WhisperModel
import ffmpeg
import math
from typing import TypedDict

def extract_audio(file_name):
   extracted_audio = f"audio-{file_name}.wav"
   stream = ffmpeg.input(f"{file_name}.mp3")
   stream = ffmpeg.output(stream, extracted_audio)
   ffmpeg.run(stream, overwrite_output=True)
   return extracted_audio

class SegmentInfo(TypedDict):
   start: float
   end: float
   text: str

def split_segments(segments) -> list[SegmentInfo]:
   new_segments = []
   class Segment:
     def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text
      
   for segment in segments:
      time_of_middle = round((segment.start + segment.end) / 2, 2)
      segment_words = segment.text.split()
      pos_middle_segment = round(math.ceil(len(segment_words)/2), 2)

      first_half_words = ' '.join(segment_words[0:pos_middle_segment])
      second_half_words = ' '.join(segment_words[pos_middle_segment:])

      new_segments.append(Segment(start=segment.start, end=time_of_middle, text=first_half_words))
      new_segments.append(Segment(start=round(time_of_middle+.01,2), end=segment.end, text=second_half_words))

   return new_segments

def transcribe(audio):
   model = WhisperModel("small")
   segments, info = model.transcribe(audio, chunk_length=10)
   language = info[0]
   segments = list(segments)
   final_segments = split_segments(segments)
   return language, final_segments
   
def createSubtitles(txt, file_name):
   tts = gTTS(txt, lang='en')
   tts.save(f"{file_name}.mp3")
   extracted_audio = extract_audio(file_name)
   language, segments = transcribe(audio=extracted_audio)
   return segments

