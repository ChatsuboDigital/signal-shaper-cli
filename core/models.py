"""
Signalis Framework Data Models
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FieldMapping:
    """Maps source CSV columns to the 6 standard export fields."""
    signal: Optional[str] = None
    domain: Optional[str] = None
    company_description: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None

    def get_mapped_fields(self) -> dict:
        return {k: v for k, v in vars(self).items() if v is not None}

    def is_complete(self) -> bool:
        return bool(self.domain or self.company_name)
