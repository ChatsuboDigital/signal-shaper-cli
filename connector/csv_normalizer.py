"""
CSV Normalization Module

Python port of connector-os/src/normalization/csv.ts
Transforms validated CSV rows into NormalizedRecord with dual keys.
"""

import re
import hashlib
from typing import List, Dict, Any, Tuple, Literal
import pandas as pd

from .models import NormalizedRecord, SignalMeta


def simple_hash(text: str) -> str:
    """Simple hash function for stable keys"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def clean_domain(domain: str) -> str:
    """
    Clean domain: strip protocol, www, path/query/hash, lowercase.
    Matches Phase 1 normalization.
    """
    if not domain:
        return ""

    cleaned = domain.strip()
    # Remove protocol
    cleaned = re.sub(r'^https?://', '', cleaned, flags=re.IGNORECASE)
    # Remove www.
    cleaned = re.sub(r'^www\.', '', cleaned, flags=re.IGNORECASE)
    # Remove path/query/hash
    cleaned = cleaned.split('/')[0].split('?')[0].split('#')[0]
    # Lowercase
    return cleaned.lower()


def parse_name(full_name: str) -> Tuple[str, str]:
    """Parse full name into first and last name"""
    parts = full_name.strip().split()
    if len(parts) == 0:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def compute_record_key(upload_id: str, side: str, row_index: int) -> str:
    """
    Compute recordKey for a CSV row.
    Format: csvu:{uploadId}:{side}:{rowIndex}
    """
    return f"csvu:{upload_id}:{side}:{row_index}"


def compute_stable_key(full_name: str, company: str, domain: str, side: str) -> str:
    """
    Compute stableKey for a CSV row.
    Format: csvs:{side}:{hash(canonical)}

    Canonical string: fullName|company|domain (all lowercased, trimmed)
    """
    canonical = "|".join([
        full_name.strip().lower(),
        company.strip().lower(),
        domain.strip().lower(),
    ])
    return f"csvs:{side}:{simple_hash(canonical)}"


def normalize_csv_records(
    df: pd.DataFrame,
    side: Literal['demand', 'supply'],
    upload_id: str
) -> Tuple[List[NormalizedRecord], List[str]]:
    """
    Normalize validated CSV rows into NormalizedRecord list.

    Args:
        df: Validated CSV dataframe from Phase 1
        side: 'demand' or 'supply'
        upload_id: Unique upload session ID

    Returns:
        Tuple of (records, stable_keys)

    INVARIANT: Pure function, no side effects, deterministic output.
    """
    records = []
    stable_keys = []

    for row_index, row in df.iterrows():
        # Extract fields from CSV row
        full_name = str(row.get('Full Name', '') or row.get('full_name', '') or '')
        company = str(row.get('Company Name', '') or row.get('company_name', '') or '')
        raw_domain = str(row.get('Domain', '') or row.get('domain', '') or '')
        title = str(row.get('Title', '') or row.get('title', '') or '')
        email = row.get('Email') or row.get('email') or None
        linkedin = row.get('LinkedIn URL') or row.get('linkedin_url') or None

        # CHECKPOINT 3: companyDescription from multiple possible columns
        description = (
            row.get('Context') or
            row.get('Service Description') or
            row.get('service_description') or
            row.get('Company Description') or
            row.get('company_description') or
            row.get('description') or
            row.get('Description') or
            row.get('about') or
            row.get('summary') or
            row.get('Notes') or
            None
        )

        # CHECKPOINT 2: Extract explicit Signal column
        explicit_signal = (
            row.get('Signal') or
            row.get('signal') or
            row.get('Hiring Signal') or
            row.get('hiring_signal') or
            ''
        )

        # Clean domain
        domain = clean_domain(raw_domain)

        # Parse name
        first_name, last_name = parse_name(full_name)

        # Compute keys
        record_key = compute_record_key(upload_id, side, row_index)
        stable_key = compute_stable_key(full_name, company, domain, side)

        # CHECKPOINT 2: Derive signalMeta from Signal column
        is_hiring_signal = bool(explicit_signal and re.match(r'^hiring[:\s]', explicit_signal, re.IGNORECASE))

        if is_hiring_signal:
            signal_meta = SignalMeta(kind='HIRING_ROLE', label=explicit_signal, source='Signal')
        elif explicit_signal:
            signal_meta = SignalMeta(kind='GROWTH', label=explicit_signal, source='Signal')
        else:
            # Fallback to title-based contact role
            contact_title = title or ('Decision maker' if side == 'demand' else 'Service provider')
            signal_meta = SignalMeta(kind='CONTACT_ROLE', label=contact_title, source='csv')

        # Determine domain source
        domain_source = 'explicit' if domain else 'none'

        # Build NormalizedRecord
        record = NormalizedRecord(
            # Identity
            record_key=record_key,

            # Contact
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            email=str(email) if email and pd.notna(email) else None,
            email_source='csv',
            email_verified=False,
            verified_by=None,
            verified_at=None,
            title=title if title else None,
            linkedin=str(linkedin) if linkedin and pd.notna(linkedin) else None,
            headline=None,
            seniority_level=None,

            # Company
            company=company,
            domain=domain,
            domain_source=domain_source,
            industry=None,
            size=None,
            company_description=str(description) if description and pd.notna(description) else None,
            company_funding=None,
            company_revenue=None,
            company_founded_year=None,
            company_linkedin=None,

            # Signal
            signal_meta=signal_meta,
            signal=explicit_signal or title or '',
            signal_detail=None,

            # Location
            city=None,
            state=None,
            country=None,

            # Meta
            schema_id='csv-upload',
            raw={
                **row.to_dict(),
                '_csv': True,
                '_uploadId': upload_id,
                '_side': side,
                '_rowIndex': row_index,
                '_stableKey': stable_key,
                '_dataSource': 'csv',
            }
        )

        records.append(record)
        stable_keys.append(stable_key)

    return records, stable_keys


def load_and_normalize_csv(
    file_path: str,
    side: Literal['demand', 'supply'],
    upload_id: str
) -> Tuple[List[NormalizedRecord], List[str]]:
    """
    Load CSV file and normalize records.

    Args:
        file_path: Path to CSV file
        side: 'demand' or 'supply'
        upload_id: Unique upload session ID

    Returns:
        Tuple of (records, stable_keys)
    """
    df = pd.read_csv(file_path)
    return normalize_csv_records(df, side, upload_id)
