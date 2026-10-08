from sqlalchemy import inspect, select

from app.database import Base, make_engine, make_session_factory
from app.models import Video


def test_table_name_matches_django():
    assert Video.__tablename__ == "shorts_video"


def test_str():
    video = Video(subreddit="AITA", post_title="Why?", content="", file_name="", video_choice="")
    assert str(video) == "Post from r/AITA named Why?"


def test_round_trip(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'db.sqlite3'}")
    Base.metadata.create_all(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        session.add(Video(subreddit="a", post_title="b", content="c", file_name="d", video_choice="e"))
        session.commit()
    with session_factory() as session:
        video = session.scalars(select(Video)).one()
    assert (video.id, video.subreddit, video.video_choice) == (1, "a", "e")
    columns = {c["name"] for c in inspect(engine).get_columns("shorts_video")}
    assert columns == {"id", "subreddit", "post_title", "content", "file_name", "video_choice"}


def test_ids_are_not_reused_after_delete(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'db.sqlite3'}")
    Base.metadata.create_all(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        first = Video(subreddit="a", post_title="b", content="c", file_name="d", video_choice="e")
        session.add(first)
        session.commit()
        session.delete(first)
        session.commit()
        second = Video(subreddit="a", post_title="b", content="c", file_name="d", video_choice="e")
        session.add(second)
        session.commit()
        assert second.id == 2

