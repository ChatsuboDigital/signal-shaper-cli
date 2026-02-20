"""
Signalis Configuration
Centralized configuration management
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from ._version import __version__


class ShaperConfig:
    """
    Centralized configuration for Signalis.
    Loads from .env and provides typed access to all settings.
    """

    def __init__(self, env_file: Optional[Path] = None):
        if env_file is None:
            env_file = Path(__file__).parent.parent / '.env'

        if env_file.exists():
            load_dotenv(env_file)

        # Framework settings
        self.framework_name = "Signalis"
        self.framework_version = __version__

        # Paths
        self.root_dir = Path(__file__).parent.parent

        # Output directory from .env or default
        output_dir_env = os.getenv('OUTPUT_DIR', 'output')
        if Path(output_dir_env).is_absolute():
            self.output_dir = Path(output_dir_env)
        else:
            self.output_dir = self.root_dir / output_dir_env

        self.shaper_output_dir = self.output_dir

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # API Keys - Apify
        self.apify_api_token = os.getenv('APIFY_API_TOKEN', '')

        # API Keys - AI Providers (for Exa signal synthesis)
        self.ai_provider = os.getenv('AI_PROVIDER', 'openai')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')

        # API Keys - Exa (Signal Generation + Domain Resolution)
        self.exa_api_key = os.getenv('EXA_API_KEY', '')

    @property
    def has_apify(self) -> bool:
        return bool(self.apify_api_token)

    @property
    def has_exa(self) -> bool:
        return bool(self.exa_api_key)

    @property
    def has_ai_provider(self) -> bool:
        if self.ai_provider == 'openai':
            return bool(self.openai_api_key)
        elif self.ai_provider == 'anthropic':
            return bool(self.anthropic_api_key)
        return False

    def get_output_dir(self, tool: Optional[str] = None) -> Path:
        return self.output_dir

    def get_config_status(self) -> Dict[str, Any]:
        return {
            'framework': {
                'name': self.framework_name,
                'version': self.framework_version
            },
            'shaper': {
                'apify': self.has_apify,
                'exa_signals': self.has_exa,
                'ai_provider': self.has_ai_provider
            }
        }

    def __repr__(self) -> str:
        status = self.get_config_status()
        return f"ShaperConfig({status['shaper']})"


# Global config instance
_config: Optional[ShaperConfig] = None


def get_config() -> ShaperConfig:
    global _config
    if _config is None:
        _config = ShaperConfig()
    return _config


def reload_config(env_file: Optional[Path] = None) -> ShaperConfig:
    global _config
    _config = ShaperConfig(env_file)
    return _config
