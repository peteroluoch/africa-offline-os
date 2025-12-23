"""
Configuration Tests - TASK 0.1
Tests for mobile-friendly, environment-driven configuration.

Following TDD: These tests are written FIRST and should FAIL initially.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from aos.core.config import Settings


class TestConfigDefaults:
    """Test that config loads with safe, mobile-friendly defaults."""

    def test_config_loads_without_env_vars(self) -> None:
        """Config must work without any environment variables (mobile-first)."""
        # Clear any AOS_ env vars
        for key in list(os.environ.keys()):
            if key.startswith("AOS_"):
                del os.environ[key]

        settings = Settings()
        
        # Verify defaults are set
        assert settings.environment == "development"
        assert settings.sqlite_path == "aos.db"
        assert settings.jwt_issuer == "aos"

    def test_default_paths_are_relative(self) -> None:
        """Default paths must be relative, not absolute (mobile constraint)."""
        settings = Settings()
        
        # DB path should be relative
        db_path = Path(settings.sqlite_path)
        assert not db_path.is_absolute(), "DB path must be relative for mobile compatibility"

    def test_config_uses_safe_defaults_for_mobile(self) -> None:
        """Config must use paths that work on Android/Termux."""
        settings = Settings()
        
        # Should not use /var, /etc, or other Linux-specific paths
        forbidden_prefixes = ["/var", "/etc", "/usr", "/opt"]
        for prefix in forbidden_prefixes:
            assert not settings.sqlite_path.startswith(prefix), \
                f"Path must not use {prefix} (not available on mobile)"


class TestConfigEnvironmentOverrides:
    """Test that all settings can be overridden via environment variables."""

    def test_sqlite_path_override(self) -> None:
        """AOS_SQLITE_PATH must override default DB path."""
        custom_path = "/custom/path/db.sqlite"
        os.environ["AOS_SQLITE_PATH"] = custom_path
        
        try:
            settings = Settings()
            assert settings.sqlite_path == custom_path
        finally:
            del os.environ["AOS_SQLITE_PATH"]

    def test_environment_override(self) -> None:
        """AOS_ENVIRONMENT must override default environment."""
        os.environ["AOS_ENVIRONMENT"] = "production"
        
        try:
            settings = Settings()
            assert settings.environment == "production"
        finally:
            del os.environ["AOS_ENVIRONMENT"]

    def test_jwt_issuer_override(self) -> None:
        """AOS_JWT_ISSUER must override default issuer."""
        custom_issuer = "custom-node-001"
        os.environ["AOS_JWT_ISSUER"] = custom_issuer
        
        try:
            settings = Settings()
            assert settings.jwt_issuer == custom_issuer
        finally:
            del os.environ["AOS_JWT_ISSUER"]


class TestConfigPathValidation:
    """Test that config validates path accessibility (mobile constraint)."""

    def test_config_validates_writable_paths(self, tmp_path: Path) -> None:
        """Config must validate that DB path is writable."""
        # This test will be implemented when we add validation logic
        # For now, it documents the requirement
        pytest.skip("Path validation not yet implemented - TDD RED phase")

    def test_config_suggests_fallback_for_readonly(self) -> None:
        """Config must suggest fallback if path is read-only."""
        # This test will be implemented when we add fallback logic
        pytest.skip("Fallback logic not yet implemented - TDD RED phase")
