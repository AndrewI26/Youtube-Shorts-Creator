from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Video
from .serlializers import VideoSerializer
from rest_framework import serializers
from rest_framework import status, settings
from django.http import FileResponse, Http404
import subprocess
from time import sleep

@api_view(['GET'])
def ApiOverview(request):
	api_urls = {
		'all_videos': '/',
		'Search by Post Title': '/?post_title=post_title',
		'Search by Video Choice': '/?videochoice=category_name',
		'Add': '/create',
		'Delete': '/item/pk/delete'
	}

	return Response(api_urls)

@api_view(['POST'])
def add_videos(request):
    video = VideoSerializer(data=request.data)
    video.is_valid()
    video.save()
    try:
        script_path = "script/createFinalVideo.py"
        args = [
            request.data['subreddit'],
            request.data['post_title'],
            request.data['content'],
            request.data['file_name'],
            request.data['video_choice']
        ]
        result = subprocess.run(['python', script_path] + args, capture_output=True, text=True)
        print(result.stderr)
    except Exception as e:
        print(e)
    
    sleep(6)
    path = f'short-{request.data['file_name']}.mp4'
    return FileResponse(open(path, 'rb'), as_attachment=True, filename='short.mp4')

@api_view(['GET'])
def view_videos(request):
    videos = Video.objects.all()

    if videos:
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data)
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)
    


