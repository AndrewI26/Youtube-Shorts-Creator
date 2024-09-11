# python3 createVideo.py
from moviepy.editor import *
from createSubtitles import createSubtitles
import os
from time import sleep

def delete_file(file_path):
    try:
        # Check if the file exists
        if os.path.isfile(file_path):
            os.remove(file_path)  # Delete the file
            print(f"File {file_path} has been deleted")
        else:
            print(f"File {file_path} does not exist")
    except Exception as e:
        print(f"An error occurred: {e}")

def createVideo(subtitles, video_choice, file_name):
    choice_to_file = {
        "subwaySurfers": "script/SubwaySurfers.mov",
        "minecraftParkor": "script/MinecraftParkor.mov",
        "mobileGame": "script/MobileGamplay.mov",
    }
    clip = VideoFileClip(choice_to_file[video_choice])
    clip = clip.subclip(0, subtitles[len(subtitles) - 1].end) 

    audio = AudioFileClip(f"{file_name}.mp3")
    clip = clip.set_audio(audio)
    

    txt_clips = []
    for segment in subtitles:
        txt_clip = TextClip(txt = segment.text, fontsize = 90, size = (800, 0), color = 'white', font = 'Futura-Bold', stroke_color = 'black', stroke_width = 5, method='caption') 
        txt_clip = txt_clip.set_position(('center', 'center'))
        txt_clip = txt_clip.set_duration(segment.end - segment.start)
        txt_clip = txt_clip.set_start(segment.start, change_end=True)  
        txt_clips.append(txt_clip)
    
    video = CompositeVideoClip([clip, *txt_clips])  

    sleep(5)
    video.write_videofile(f"short-{file_name}.mp4", fps = 30)
    video.close()
    audio.close()
    for txt_clip in txt_clips:
        txt_clip.close()

    #delete_file(f"{file_name}.mp3")
    #delete_file(f"audio-{file_name}.wav")
    #try: 
        #delete_file(f"short-{file_name}TEMP_MPY_wvf_snd.mp3")
    #except Exception as e:
       # print(e)

    

