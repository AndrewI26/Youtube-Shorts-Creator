import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.database import make_engine, make_session_factory
from app.models import Video


def make_video(**overrides):
    fields = dict(subreddit="a", post_title="b", content="c", file_name="d", video_choice="e")
    return Video(**{**fields, **overrides})


@pytest.fixture
def session_factory(clean_db):
    return make_session_factory(clean_db)


def test_table_name():
    assert Video.__tablename__ == "videos"


def test_str():
    video = make_video(subreddit="AITA", post_title="Why?")
    assert str(video) == "Post from r/AITA named Why?"


def test_round_trip(session_factory):
    with session_factory() as session:
        session.add(make_video())
        session.commit()
    with session_factory() as session:
        video = session.scalars(select(Video)).one()
    assert (video.id, video.subreddit, video.video_choice) == (1, "a", "e")


def test_schema_matches_model(clean_db):
    columns = {c["name"]: c for c in inspect(clean_db).get_columns("videos")}
    assert set(columns) == {"id", "subreddit", "post_title", "content", "file_name", "video_choice"}
    assert not any(c["nullable"] for c in columns.values())
    assert columns["id"]["identity"] is not None
    assert columns["subreddit"]["type"].length == 255
    assert columns["file_name"]["type"].length == 225


def test_ids_are_not_reused_after_delete(session_factory):
    with session_factory() as session:
        first = make_video()
        session.add(first)
        session.commit()
        session.delete(first)
        session.commit()
        second = make_video()
        session.add(second)
        session.commit()
        assert second.id == 2


@pytest.mark.parametrize("field", ["subreddit", "post_title", "content", "file_name", "video_choice"])
def test_columns_are_not_nullable(session_factory, field):
    with session_factory() as session:
        session.add(make_video(**{field: None}))
        with pytest.raises(IntegrityError):
            session.commit()


def test_subreddit_length_is_enforced_by_postgres(session_factory):
    from sqlalchemy.exc import DataError

    with session_factory() as session:
        session.add(make_video(subreddit="x" * 256))
        with pytest.raises(DataError):
            session.commit()


def test_engine_uses_psycopg_and_pre_ping(database_url):
    engine = make_engine(database_url)
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()
