"""
Enrichment Cache - File-based caching for enriched contacts

Uses JSON file for simplicity. 90-day TTL.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .models import NormalizedRecord, EnrichmentResult


# Cache settings
CACHE_FILE = Path.home() / '.signalis' / 'enrichment_cache.json'
CACHE_TTL_DAYS = 90  # 90-day TTL like original


@dataclass
class CachedContact:
    """Cached enrichment result"""
    email: str
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    source: str = ""
    enriched_at: str = ""  # ISO timestamp
    verified: bool = False


def compute_cache_key(record: NormalizedRecord) -> str:
    """
    Generate stable cache key for a record.

    Port of connector-os/src/enrichment/recordKey.ts
    Priority-based fallback chain:
    1. recordKey (if set)
    2. domain → "d:<domain>"
    3. company + person → "p:<slug>|<slug>"
    4. company only → "c:<slug>"
    5. hash fallback → "x:<hash>"
    """
    # Priority 1: Use recordKey if set
    if record.record_key:
        return record.record_key

    # Priority 2: Domain-based
    if record.domain:
        return f"d:{record.domain.lower()}"

    # Priority 3: Person + Company
    if record.full_name and record.company:
        person_slug = slugify(record.full_name)
        company_slug = slugify(record.company)
        return f"p:{person_slug}|{company_slug}"

    # Priority 4: Company only
    if record.company:
        company_slug = slugify(record.company)
        return f"c:{company_slug}"

    # Priority 5: Hash fallback
    canonical = f"{record.full_name}|{record.company}|{record.email or ''}"
    hash_val = simple_hash(canonical)
    return f"x:{hash_val}"


def slugify(text: str) -> str:
    """Convert text to slug (lowercase, alphanumeric, spaces->dashes)"""
    # Lowercase
    slug = text.lower()
    # Replace spaces with dashes
    slug = slug.replace(' ', '-')
    # Keep only alphanumeric and dashes
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    # Remove duplicate dashes
    while '--' in slug:
        slug = slug.replace('--', '-')
    # Trim dashes
    slug = slug.strip('-')
    # Max 50 chars
    return slug[:50]


def simple_hash(text: str) -> str:
    """Simple deterministic hash for cache keys"""
    # Use MD5 for deterministic hashing (not cryptographic use)
    return hashlib.md5(text.encode()).hexdigest()[:8]


def load_cache() -> Dict[str, CachedContact]:
    """Load cache from file"""
    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)

        # Convert to CachedContact objects
        cache = {}
        for key, value in data.items():
            cache[key] = CachedContact(**value)

        return cache
    except Exception:
        return {}


def save_cache(cache: Dict[str, CachedContact]) -> None:
    """Save cache to file"""
    # Create directory if needed
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict
    data = {key: asdict(contact) for key, contact in cache.items()}

    # Write to file
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def is_cache_stale(enriched_at: str) -> bool:
    """Check if cache entry is stale (>90 days old)"""
    try:
        enriched_time = datetime.fromisoformat(enriched_at.replace('Z', '+00:00'))
        age = datetime.now(enriched_time.tzinfo) - enriched_time
        return age > timedelta(days=CACHE_TTL_DAYS)
    except Exception:
        return True  # Treat invalid timestamps as stale


def check_cache(record: NormalizedRecord) -> Optional[EnrichmentResult]:
    """
    Check cache for existing enrichment result.
    Returns cached result if found and not stale.
    """
    cache_key = compute_cache_key(record)
    cache = load_cache()

    cached = cache.get(cache_key)
    if not cached:
        return None

    # Check if stale
    if is_cache_stale(cached.enriched_at):
        return None

    # Return as EnrichmentResult
    return EnrichmentResult(
        action='VERIFY',
        outcome='ENRICHED',
        email=cached.email,
        source=cached.source,
        first_name=cached.first_name,
        last_name=cached.last_name,
        title=cached.title,
        inputs_present={'cached': True}
    )


def store_in_cache(record: NormalizedRecord, result: EnrichmentResult) -> None:
    """
    Store enrichment result in cache.
    Only stores successful enrichments with emails.
    """
    # Only cache successful enrichments
    if result.outcome not in ['ENRICHED', 'VERIFIED']:
        return

    # Must have email
    if not result.email:
        return

    # Don't cache pre-existing or none sources
    if result.source in ['none', 'existing']:
        return

    # Generate cache key
    cache_key = compute_cache_key(record)

    # Load current cache
    cache = load_cache()

    # Create cached contact
    cached = CachedContact(
        email=result.email,
        first_name=result.first_name or record.first_name or "",
        last_name=result.last_name or record.last_name or "",
        title=result.title or record.title or "",
        source=result.source,
        enriched_at=datetime.utcnow().isoformat() + 'Z',
        verified=result.outcome == 'VERIFIED'
    )

    # Store in cache
    cache[cache_key] = cached

    # Save to file
    save_cache(cache)


def clear_cache() -> None:
    """Clear the entire enrichment cache"""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    cache = load_cache()

    total = len(cache)
    stale = sum(1 for c in cache.values() if is_cache_stale(c.enriched_at))
    fresh = total - stale

    sources = {}
    for contact in cache.values():
        sources[contact.source] = sources.get(contact.source, 0) + 1

    return {
        'total': total,
        'fresh': fresh,
        'stale': stale,
        'by_source': sources,
        'cache_file': str(CACHE_FILE),
    }
