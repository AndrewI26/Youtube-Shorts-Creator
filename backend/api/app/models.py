from sqlalchemy import BigInteger, Identity, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    subreddit: Mapped[str] = mapped_column(String(255))
    post_title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String(225))
    video_choice: Mapped[str] = mapped_column(String(500))

    def __str__(self) -> str:
        return f"Post from r/{self.subreddit} named {self.post_title}"
