"""
Configuration Management
========================

Centralized configuration using Pydantic ``BaseSettings``. Configuration
values are loaded in the following priority order (highest wins):

    1. Environment variables
    2. ``.env`` file (if present)
    3. ``config/default.yaml`` (platform defaults)
    4. Hardcoded defaults in this module

This module provides a singleton ``get_settings()`` function that caches
the ``Settings`` instance for the lifetime of the application.

Usage::

    from src.core.config import get_settings

    settings = get_settings()
    print(settings.database_url)
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


# Project root is two levels up from this file (src/core/config.py → project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application-wide settings.

    All settings can be overridden via environment variables. Environment
    variable names are the UPPERCASE version of the attribute name
    (e.g., ``app_name`` → ``APP_NAME``).

    Attributes:
        app_name: Display name of the platform.
        app_env: Deployment environment (development, staging, production).
        debug: Enable debug mode (verbose logging, auto-reload).
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).

        api_host: FastAPI server bind address.
        api_port: FastAPI server bind port.
        api_prefix: URL prefix for all API routes.

        database_url: SQLAlchemy-compatible database URL.

        streamlit_port: Streamlit UI server port.
        api_base_url: Base URL for the FastAPI server (used by Streamlit).

        reports_dir: Directory for generated report files.
        test_cases_dir: Directory for uploaded test case files.
        config_dir: Directory for YAML configuration files.

        langfuse_enabled: Whether to send traces to Langfuse.
        langfuse_public_key: Langfuse project public key.
        langfuse_secret_key: Langfuse project secret key.
        langfuse_host: Langfuse server URL.
    """

    # Application
    app_name: str = "Generic AI Testing Platform"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # FastAPI
    api_host: str = "::"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = Field(
        default=f"sqlite:///{PROJECT_ROOT / 'data' / 'platform.db'}"
    )

    # Streamlit
    streamlit_port: int = 8501
    api_base_url: str = "http://localhost:8000"

    # Directories
    reports_dir: Path = PROJECT_ROOT / "reports"
    test_cases_dir: Path = PROJECT_ROOT / "testcases"
    config_dir: Path = PROJECT_ROOT / "config"

    # Langfuse (Milestone 2+)
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Uses ``@lru_cache`` to ensure settings are loaded exactly once.
    To reload settings (e.g., in tests), call ``get_settings.cache_clear()``.

    Returns:
        The application Settings instance.
    """
    return Settings()
