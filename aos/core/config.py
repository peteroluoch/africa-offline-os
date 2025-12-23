from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AOS_", extra="ignore")

    environment: str = "development"
    sqlite_path: str = "aos.db"
    jwt_issuer: str = "aos"
