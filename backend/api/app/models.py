from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Video(Base):
    # Same table the Django app used, so the existing db.sqlite3 keeps working.
    __tablename__ = "shorts_video"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    subreddit: Mapped[str] = mapped_column(String(255))
    post_title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String(225))
    video_choice: Mapped[str] = mapped_column(String(500))

    def __str__(self) -> str:
        return f"Post from r/{self.subreddit} named {self.post_title}"
