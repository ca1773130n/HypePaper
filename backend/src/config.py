"""Configuration management with JSON file loading and environment variable overrides."""

import json
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


def deep_merge(base: dict, update: dict) -> dict:
    """Deep merge two dictionaries."""
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base


class Settings(BaseSettings):
    """Application settings with JSON config and environment variable support."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://localhost/hypepaper",
        validation_alias='DATABASE_URL'
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # GitHub settings
    github_token: str = Field(..., validation_alias='GITHUB_TOKEN')
    github_rate_limit: int = 5000

    # LLM settings
    llm_provider: str = Field(default='llamacpp', validation_alias='LLM_PROVIDER')
    openai_api_key: Optional[str] = Field(None, validation_alias='OPENAI_API_KEY')
    llamacpp_server: str = Field(
        default='http://localhost:10002/v1/chat/completions',
        validation_alias='LLAMACPP_SERVER'
    )

    # PDF storage
    pdf_storage_base_path: str = Field(
        default='./data/papers',
        validation_alias='PDF_STORAGE_PATH'
    )

    # App settings
    app_name: str = "HypePaper"
    app_version: str = "1.0.0"
    debug: bool = False

    @classmethod
    def load_from_json_dir(cls, config_dir: Path) -> 'Settings':
        """Load settings from JSON config directory with deep merge."""
        merged = {}

        # Load all JSON files in config directory
        if config_dir.exists():
            for json_file in sorted(config_dir.glob('*.json')):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        merged = deep_merge(merged, data)
                except Exception as e:
                    print(f"Warning: Failed to load {json_file}: {e}")

        # Flatten nested config structure for Pydantic
        flat_config = {}

        # Database config
        if 'database' in merged:
            db = merged['database']
            if 'url' in db:
                flat_config['database_url'] = db['url']
            if 'pool_size' in db:
                flat_config['database_pool_size'] = db['pool_size']
            if 'max_overflow' in db:
                flat_config['database_max_overflow'] = db['max_overflow']

        # LLM config
        if 'llm' in merged:
            llm = merged['llm']
            if 'provider' in llm:
                flat_config['llm_provider'] = llm['provider']
            if 'llamacpp_server' in llm:
                flat_config['llamacpp_server'] = llm['llamacpp_server']

        # GitHub config
        if 'github' in merged:
            gh = merged['github']
            if 'rate_limit_per_hour' in gh:
                flat_config['github_rate_limit'] = gh['rate_limit_per_hour']

        # PDF storage
        if 'pdf_storage' in merged and 'base_path' in merged['pdf_storage']:
            flat_config['pdf_storage_base_path'] = merged['pdf_storage']['base_path']

        # App config
        if 'app' in merged:
            app = merged['app']
            if 'name' in app:
                flat_config['app_name'] = app['name']
            if 'version' in app:
                flat_config['app_version'] = app['version']
            if 'debug' in app:
                flat_config['debug'] = app['debug']

        # Environment variables override JSON settings
        # Pydantic will automatically apply env var overrides
        return cls(**flat_config)


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global settings
    if settings is None:
        config_dir = Path(__file__).parent.parent / 'configs'
        try:
            settings = Settings.load_from_json_dir(config_dir)
        except Exception:
            # Fallback to defaults if config loading fails
            settings = Settings(github_token=os.getenv('GITHUB_TOKEN', 'PLACEHOLDER'))
    return settings
