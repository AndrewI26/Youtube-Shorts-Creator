from django.db import models

# Create your models here.

class Video(models.Model):
    subreddit = models.CharField(max_length=1000)
    post_title = models.TextField()
    content = models.TextField()
    file_name = models.CharField(max_length=1000)
    video_choice = models.CharField(choices=(("subwaySurfers", "subwaySurfers"), ("minecraftParkor", "minecraftParkor"), ("mobileGame", "mobileGame")), max_length=500)

    def __str__(self) -> str:
        return f"Post from r/{self.subreddit} named {self.post_title}"