"""
Basic field normalization

Handles common data cleaning:
- Trim whitespace
- Collapse multiple spaces
- Remove null/None/empty values
- Lowercase for specific fields
"""

from typing import Any


def normalize_field(value: Any, field_type: str = 'text') -> str:
    """
    Normalize a single field value.

    Args:
        value: Raw field value
        field_type: Type of field ('text', 'email', 'domain', 'name')

    Returns:
        Normalized string value
    """
    # Handle None, empty, or whitespace-only values
    if value is None or value == '':
        return ''

    # Convert to string
    text = str(value).strip()

    if not text:
        return ''

    # Collapse multiple spaces
    text = ' '.join(text.split())

    # Apply type-specific normalization
    if field_type == 'email':
        # Lowercase emails
        text = text.lower()

    elif field_type == 'domain':
        # Handled by domain_normalizer.py
        pass

    elif field_type == 'name':
        # Title case for names (e.g., "john doe" -> "John Doe")
        # But preserve existing capitalization if reasonable
        if text.islower() or text.isupper():
            text = text.title()

    return text
