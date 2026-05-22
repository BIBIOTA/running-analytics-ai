from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    strava_client_id: str
    strava_client_secret: str
    gemini_api_key: str
    mongodb_uri: str
    jwt_secret: str
    encryption_key: str
    frontend_url: str = "http://localhost:3000"
    mongodb_database: str = "running_analytics"
    gemini_model: str = "gemini-3.1-pro-preview"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
