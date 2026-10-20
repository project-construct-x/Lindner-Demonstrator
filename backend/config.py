import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent
EPCIS_TEMPLATES_DIR = BACKEND_DIR / "epcis"


def _env_files() -> tuple[Path, ...]:
    stage = os.environ.get("APP_ENV", "development")
    candidates = (
        BACKEND_DIR / f".env.{stage}.local",
        BACKEND_DIR / f".env.{stage}",
        BACKEND_DIR / ".env",
    )
    return tuple(path for path in candidates if path.is_file())


class Settings(BaseSettings):
    app_env: str = "development"
    output_dir: Path = Field(default=Path("output"))
    log_level: str = "INFO"
    cors_origins: str = "*"
    epcat_base_url: str = ""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def events_dir(self) -> Path:
        path = self.output_dir
        return path if path.is_absolute() else BACKEND_DIR / path


@lru_cache
def get_settings() -> Settings:
    files = _env_files()
    return Settings(_env_file=files or None)


settings = get_settings()
OUTPUT_DIR = settings.events_dir
EVENTS_DIR = OUTPUT_DIR
