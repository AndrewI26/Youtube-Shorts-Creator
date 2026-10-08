from pathlib import Path

import pytest

from app.config import BASE_DIR, Settings

ENV_VARS = ["DATABASE_URL", "MEDIA_DIR", "BACKGROUNDS_DIR", "WHISPER_MODEL", "CAPTION_FONT", "CORS_ORIGINS"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_defaults_point_inside_backend():
    settings = Settings.from_env()
    assert settings.database_url == f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    assert settings.media_dir == BASE_DIR / "media"
    assert settings.backgrounds_dir == BASE_DIR / "assets" / "backgrounds"
    assert settings.whisper_model == "small"
    assert settings.caption_font == "Futura-Bold"
    assert settings.cors_origins == ["*"]


def test_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///other.db")
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "m"))
    monkeypatch.setenv("BACKGROUNDS_DIR", str(tmp_path / "b"))
    monkeypatch.setenv("WHISPER_MODEL", "medium")
    monkeypatch.setenv("CAPTION_FONT", "/fonts/x.ttf")
    settings = Settings.from_env()
    assert settings.database_url == "sqlite:///other.db"
    assert settings.media_dir == tmp_path / "m"
    assert settings.backgrounds_dir == tmp_path / "b"
    assert isinstance(settings.backgrounds_dir, Path)
    assert settings.whisper_model == "medium"
    assert settings.caption_font == "/fonts/x.ttf"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("http://a.com", ["http://a.com"]),
        ("http://a.com,http://b.com", ["http://a.com", "http://b.com"]),
        (" http://a.com , http://b.com ,", ["http://a.com", "http://b.com"]),
        ("", ["*"]),
        (" , ", ["*"]),
    ],
)
def test_cors_origins_parsing(monkeypatch, raw, expected):
    monkeypatch.setenv("CORS_ORIGINS", raw)
    assert Settings.from_env().cors_origins == expected


def test_settings_are_immutable():
    with pytest.raises(Exception):
        Settings().whisper_model = "large"
