"""Package Config."""

from functools import cache

from pydantic import BaseModel, ConfigDict, SecretStr
from pydantic_settings import BaseSettings


class TflSettings(BaseModel):
    """TfL specific settings."""

    app_id: str
    app_key: SecretStr


class Settings(BaseSettings):
    """App wide settings."""

    tfl: TflSettings

    model_config = ConfigDict(
        env_file_encoding="utf-8",
        env_file=".env",
        env_nested_delimiter="__",
    )


@cache
def get_settings() -> Settings:
    """Access cached Settings()."""
    return Settings()
