"""
Configuration Module - TASK 0.1
Mobile-friendly, environment-driven configuration for Africa Offline OS.

This module provides safe defaults that work on:
- Linux (standard servers)
- Raspberry Pi (edge devices)
- Android (Termux runtime)

All paths are relative by default to support mobile deployments.
All settings can be overridden via AOS_* environment variables.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with mobile-first defaults.
    
    All settings can be overridden via environment variables with AOS_ prefix.
    Example: AOS_SQLITE_PATH=/custom/path/db.sqlite
    
    Attributes:
        environment: Runtime environment (development/production)
        sqlite_path: Path to SQLite database (relative by default)
        jwt_issuer: JWT token issuer identifier
    """

    model_config = SettingsConfigDict(
        env_prefix="AOS_",
        extra="ignore",
        case_sensitive=False,
    )

    # Runtime environment
    environment: str = "development"

    # Database configuration (mobile-friendly relative path)
    sqlite_path: str = "aos.db"

    # Path configuration
    data_dir: str = "data"
    keys_dir: str = "data/keys"

    # Security configuration
    jwt_issuer: str = "aos"
    master_secret: str = "change-this-in-production-use-aos-master-secret"
    kdf_iterations: int = 100000  # PBKDF2 iterations for key derivation

    # Resource configuration
    resource_check_interval: int = 30

    # Africa's Talking configuration
    at_username: str = "sandbox"
    at_api_key: str = ""
    at_environment: str = "sandbox"  # sandbox or production


settings = Settings()
