"""Signalis Framework Core"""

from .config import ShaperConfig, get_config, reload_config
from .models import FieldMapping

__version__ = "1.0.0"

__all__ = [
    'ShaperConfig', 'get_config', 'reload_config',
    'FieldMapping',
]
