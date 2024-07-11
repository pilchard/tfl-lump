"""Package Config."""

from functools import cache
from typing import Annotated

from pydantic import AfterValidator, BaseModel, HttpUrl, SecretStr
from pydantic_settings import BaseSettings

HttpUrlString = Annotated[HttpUrl, AfterValidator(str)]


class TflSettings(BaseModel):
    """TfL specific settings."""

    app_id: str
    app_key: SecretStr
    base_url: HttpUrlString


class Settings(BaseSettings):
    """App wide settings."""

    tfl: TflSettings

    class Config:
        """Pydantic settings config."""

        env_file_encoding = "utf-8"
        env_file = ".env"
        env_nested_delimiter = "__"


@cache
def get_settings() -> Settings:
    """Access cached Settings()."""
    return Settings()


if __name__ == "__main__":
    print(Settings().model_dump())
