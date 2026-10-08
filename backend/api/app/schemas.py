from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class VideoChoice(str, Enum):
    SUBWAY_SURFERS = "subwaySurfers"
    MINECRAFT_PARKOR = "minecraftParkor"
    MOBILE_GAME = "mobileGame"


class VideoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    subreddit: str = Field(min_length=1, max_length=255)
    post_title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    file_name: str = Field(min_length=1, max_length=225)
    video_choice: VideoChoice


class VideoRead(BaseModel):
    # Plain strings: rows written by the old Django app are returned as-is.
    model_config = ConfigDict(from_attributes=True)

    id: int
    subreddit: str
    post_title: str
    content: str
    file_name: str
    video_choice: str
