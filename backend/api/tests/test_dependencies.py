from functools import partial

import pytest

from app.dependencies import get_video_generator, make_work_dir, remove_dir, safe_stem
from app.services.pipeline import generate_short


@pytest.mark.parametrize(
    "name, expected",
    [
        ("simple", "simple"),
        ("with space", "with-space"),
        ("I (25F) ", "I-25F"),
        ("../../etc/passwd", "etc-passwd"),
        ("a/b\\c", "a-b-c"),
        ("keep_under-score", "keep_under-score"),
        ("Ünïcödé", "n-c-d"),
        ("😬😬", "short"),
        ("", "short"),
        ("...", "short"),
        ("---", "short"),
        ("12", "12"),
    ],
)
def test_safe_stem(name, expected):
    assert safe_stem(name) == expected


def test_safe_stem_truncates():
    assert safe_stem("a" * 200) == "a" * 50
    assert safe_stem("abc", max_length=2) == "ab"


def test_safe_stem_does_not_end_with_separator_after_truncation():
    assert safe_stem("abcd efgh", max_length=5) == "abcd"


def test_make_work_dir_creates_unique_dirs(tmp_path):
    dirs = {make_work_dir(tmp_path, "same") for _ in range(20)}
    assert len(dirs) == 20
    assert all(d.is_dir() and d.parent == tmp_path for d in dirs)


def test_make_work_dir_creates_missing_media_dir(tmp_path):
    work_dir = make_work_dir(tmp_path / "nested" / "media", "x")
    assert work_dir.is_dir()


def test_remove_dir_deletes_tree(tmp_path):
    target = tmp_path / "job"
    (target / "sub").mkdir(parents=True)
    (target / "sub" / "file.mp4").write_bytes(b"x")
    remove_dir(target)
    assert not target.exists()


def test_remove_dir_ignores_missing(tmp_path):
    remove_dir(tmp_path / "missing")


def test_default_generator_is_bound_to_settings(settings):
    generator = get_video_generator(settings)
    assert isinstance(generator, partial)
    assert generator.func is generate_short
    assert generator.keywords == {"settings": settings}
