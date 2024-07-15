"""Package Config."""

from __future__ import annotations

from functools import cache

from dotenv import find_dotenv
from pydantic import BaseModel, ConfigDict, SecretStr
from pydantic_settings import BaseSettings


class TflSettings(BaseModel):
    """TfL specific settings."""

    app_id: str | None = None
    app_key: SecretStr | None = None


class Settings(BaseSettings):
    """App wide settings."""

    tfl: TflSettings | None = TflSettings()

    model_config = ConfigDict(
        env_file_encoding="utf-8",
        env_file=find_dotenv(".env"),
        env_nested_delimiter="__",
    )


@cache
def get_settings() -> Settings:
    """Access cached Settings()."""
    return Settings()
