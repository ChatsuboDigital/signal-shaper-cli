"""
Domain normalization

Cleans and standardizes domain names:
- Remove protocol (http://, https://)
- Remove www subdomain
- Remove paths, query params, fragments
- Lowercase
- Trim whitespace
"""

import re
from typing import Optional
from urllib.parse import urlparse


def normalize_domain(domain: Optional[str]) -> str:
    """
    Normalize a domain name to clean format.

    Args:
        domain: Raw domain/URL string

    Returns:
        Cleaned domain (e.g., "example.com")

    Examples:
        >>> normalize_domain("https://www.example.com/path")
        "example.com"

        >>> normalize_domain("HTTP://Example.COM")
        "example.com"

        >>> normalize_domain("www.example.com/")
        "example.com"
    """
    if not domain or not isinstance(domain, str):
        return ''

    domain = domain.strip().lower()

    if not domain:
        return ''

    # Add scheme if missing for urlparse to work correctly
    if not domain.startswith(('http://', 'https://', '//')):
        domain = f'http://{domain}'

    # Parse URL
    try:
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path
    except Exception:
        # Fallback: basic string cleaning
        domain = re.sub(r'^https?://', '', domain)
        domain = domain.split('/')[0]
        domain = domain.split('?')[0]
        domain = domain.split('#')[0]

    # Remove www subdomain
    if domain.startswith('www.'):
        domain = domain[4:]

    # Remove trailing slashes
    domain = domain.rstrip('/')

    # Remove port numbers (e.g., example.com:8080 -> example.com)
    domain = domain.split(':')[0]

    # Final validation: must have at least one dot and valid characters
    if '.' not in domain:
        return ''

    # Remove invalid characters (keep only alphanumeric, dots, hyphens)
    domain = re.sub(r'[^a-z0-9.-]', '', domain)

    return domain


def is_valid_domain(domain: str) -> bool:
    """
    Check if a domain looks valid.

    Args:
        domain: Domain string

    Returns:
        True if domain looks valid
    """
    if not domain:
        return False

    # Must have at least one dot
    if '.' not in domain:
        return False

    # Must not start or end with dot/hyphen
    if domain.startswith(('.', '-')) or domain.endswith(('.', '-')):
        return False

    # Must have valid TLD (at least 2 chars after last dot)
    parts = domain.split('.')
    if len(parts[-1]) < 2:
        return False

    # Basic pattern check
    pattern = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}$'
    return bool(re.match(pattern, domain))
