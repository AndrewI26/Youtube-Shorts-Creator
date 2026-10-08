import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    # Per-request working directories (narration audio, rendered short) live here.
    media_dir: Path = BASE_DIR / "media"
    # Folder holding SubwaySurfers.mov, MinecraftParkor.mov and MobileGamplay.mov.
    backgrounds_dir: Path = BASE_DIR / "assets" / "backgrounds"
    whisper_model: str = "small"
    # ImageMagick font name or path to a .ttf/.ttc/.otf file.
    caption_font: str = "Futura-Bold"
    cors_origins: list[str] = field(default_factory=lambda: ["*"])

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            database_url=os.getenv("DATABASE_URL", defaults.database_url),
            media_dir=Path(os.getenv("MEDIA_DIR", defaults.media_dir)),
            backgrounds_dir=Path(os.getenv("BACKGROUNDS_DIR", defaults.backgrounds_dir)),
            whisper_model=os.getenv("WHISPER_MODEL", defaults.whisper_model),
            caption_font=os.getenv("CAPTION_FONT", defaults.caption_font),
            cors_origins=_split_csv(os.getenv("CORS_ORIGINS", "*")) or ["*"],
        )
