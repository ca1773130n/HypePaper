"""
Configuration service with JSON deep merge and environment variable overrides.

Provides centralized configuration management by loading multiple JSON files
and merging them with environment variable overrides.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from ..config import Settings, deep_merge


class ConfigService:
    """
    Service for loading and managing application configuration.

    Features:
    - Load multiple JSON config files from directory
    - Deep merge configuration objects
    - Environment variable overrides via Pydantic Settings
    - Prompt template management
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration service.

        Args:
            config_dir: Directory containing JSON config files
                       (defaults to backend/configs/)
        """
        if config_dir is None:
            # Default to configs directory relative to backend/src
            config_dir = Path(__file__).parent.parent.parent / 'configs'

        self.config_dir = Path(config_dir)
        self._settings: Optional[Settings] = None
        self._prompts: Dict[str, str] = {}

    def load_config(self, config_dir: Optional[Path] = None) -> Settings:
        """
        Load configuration from JSON files with environment variable overrides.

        Loads all JSON files from config directory, merges them in alphabetical
        order, then applies environment variable overrides through Pydantic.

        Args:
            config_dir: Override default config directory

        Returns:
            Settings object with merged configuration
        """
        if config_dir:
            self.config_dir = Path(config_dir)

        # Use existing Settings class from config.py
        self._settings = Settings.load_from_json_dir(self.config_dir)

        return self._settings

    def get_settings(self) -> Settings:
        """
        Get current settings, loading if not already loaded.

        Returns:
            Settings object
        """
        if self._settings is None:
            self._settings = self.load_config()

        return self._settings

    def load_prompts(self) -> Dict[str, str]:
        """
        Load LLM prompt templates from prompts.json.

        Returns:
            Dictionary of prompt names to prompt text
        """
        prompts_file = self.config_dir / 'prompts.json'

        if not prompts_file.exists():
            return {}

        try:
            with open(prompts_file, 'r') as f:
                self._prompts = json.load(f)
            return self._prompts
        except Exception as e:
            print(f"Failed to load prompts from {prompts_file}: {e}")
            return {}

    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Get a specific prompt template by name.

        Args:
            prompt_name: Name of the prompt (e.g., 'extract_tasks')

        Returns:
            Prompt template string or None if not found
        """
        if not self._prompts:
            self.load_prompts()

        return self._prompts.get(prompt_name)

    def get_llm_prompts(self) -> Dict[str, str]:
        """
        Get all LLM prompt templates.

        Returns:
            Dictionary of all prompts
        """
        if not self._prompts:
            self.load_prompts()

        return self._prompts

    @staticmethod
    def merge_configs(configs: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deep merge multiple configuration dictionaries.

        Later dictionaries override earlier ones. Nested objects are merged
        recursively.

        Args:
            configs: List of configuration dictionaries

        Returns:
            Merged configuration dictionary

        Example:
            >>> base = {'db': {'host': 'localhost', 'port': 5432}}
            >>> override = {'db': {'port': 3000}}
            >>> ConfigService.merge_configs([base, override])
            {'db': {'host': 'localhost', 'port': 3000}}
        """
        if not configs:
            return {}

        merged = configs[0].copy()
        for config in configs[1:]:
            merged = deep_merge(merged, config)

        return merged

    def reload_config(self) -> Settings:
        """
        Reload configuration from disk.

        Useful for picking up configuration changes without restarting.

        Returns:
            Refreshed Settings object
        """
        self._settings = None
        self._prompts = {}
        return self.load_config()

    def validate_config(self) -> bool:
        """
        Validate that required configuration is present.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            settings = self.get_settings()

            # Check required fields
            if not settings.github_token:
                print("Error: GITHUB_TOKEN not configured")
                return False

            if not settings.database_url:
                print("Error: DATABASE_URL not configured")
                return False

            return True

        except Exception as e:
            print(f"Configuration validation error: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get summary of current configuration (safe for logging).

        Excludes sensitive values like API keys.

        Returns:
            Dictionary with configuration summary
        """
        settings = self.get_settings()

        return {
            'app_name': settings.app_name,
            'app_version': settings.app_version,
            'debug': settings.debug,
            'llm_provider': settings.llm_provider,
            'database_configured': bool(settings.database_url),
            'github_configured': bool(settings.github_token),
            'openai_configured': bool(settings.openai_api_key),
            'pdf_storage_path': settings.pdf_storage_base_path,
            'config_dir': str(self.config_dir)
        }


# Global singleton instance
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """
    Get or create global ConfigService instance.

    Returns:
        Singleton ConfigService instance
    """
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service
