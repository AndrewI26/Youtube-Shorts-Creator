from django.db.models import fields
from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('subreddit', 'post_title', 'content', 'file_name', 'video_choice')
