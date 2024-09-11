from createSubtitles import createSubtitles
from createVideo import createVideo
import sys
from time import sleep

def createFinalVideo(subreddit_title, post_title, post_body, file_name, video_choice):
    txt = f"From the subreddit {subreddit_title}, {post_title}. {post_body}"
    subtitles = createSubtitles(txt, file_name)
    createVideo(subtitles, video_choice, file_name)
    

if __name__ == "__main__":
   createFinalVideo(sys.argv[1], sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])

   

