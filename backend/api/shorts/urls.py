from django.urls import path

from . import views

urlpatterns = [
    path("", views.ApiOverview, name="home"),
    path('create/', views.add_videos, name='video-upload'),
    path("all/", views.view_videos, name='view_videos')
]