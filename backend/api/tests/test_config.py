from pathlib import Path

import pytest

from app.config import BASE_DIR, DEFAULT_DATABASE_URL, Settings, normalize_database_url

ENV_VARS = ["DATABASE_URL", "MEDIA_DIR", "BACKGROUNDS_DIR", "WHISPER_MODEL", "CAPTION_FONT", "CORS_ORIGINS"]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_defaults_point_inside_backend():
    settings = Settings.from_env()
    assert settings.database_url == DEFAULT_DATABASE_URL
    assert DEFAULT_DATABASE_URL.startswith("postgresql+psycopg://")
    assert settings.media_dir == BASE_DIR / "media"
    assert settings.backgrounds_dir == BASE_DIR / "assets" / "backgrounds"
    assert settings.whisper_model == "small"
    assert settings.caption_font == "Futura-Bold"
    assert settings.cors_origins == ["*"]


def test_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/other")
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "m"))
    monkeypatch.setenv("BACKGROUNDS_DIR", str(tmp_path / "b"))
    monkeypatch.setenv("WHISPER_MODEL", "medium")
    monkeypatch.setenv("CAPTION_FONT", "/fonts/x.ttf")
    settings = Settings.from_env()
    assert settings.database_url == "postgresql+psycopg://u:p@db:5432/other"
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


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("postgresql://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgres://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql+asyncpg://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),
        ("sqlite:///x.db", "sqlite:///x.db"),
    ],
)
def test_normalize_database_url(raw, expected):
    assert normalize_database_url(raw) == expected


def test_env_database_url_is_normalized(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h:5432/db")
    assert Settings.from_env().database_url == "postgresql+psycopg://u:p@h:5432/db"
