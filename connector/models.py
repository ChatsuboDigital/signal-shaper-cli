"""
Data models for Connector CLI

Python port of connector-os schemas
"""

from typing import Optional, Dict, Any, List, Literal
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SignalMeta:
    """Signal metadata from CSV"""
    kind: Literal['HIRING_ROLE', 'GROWTH', 'CONTACT_ROLE']
    label: str
    source: str


@dataclass
class NormalizedRecord:
    """Normalized record structure - matches TypeScript NormalizedRecord"""

    # Identity
    record_key: str

    # Contact
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    email: Optional[str] = None
    email_source: str = "csv"
    email_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    title: Optional[str] = None
    linkedin: Optional[str] = None
    headline: Optional[str] = None
    seniority_level: Optional[str] = None

    # Company
    company: str = ""
    domain: str = ""
    domain_source: Literal['explicit', 'derived', 'none'] = 'none'
    industry: Optional[str] = None
    size: Optional[str] = None
    company_description: Optional[str] = None
    company_funding: Optional[str] = None
    company_revenue: Optional[str] = None
    company_founded_year: Optional[int] = None
    company_linkedin: Optional[str] = None

    # Signal
    signal_meta: Optional[SignalMeta] = None
    signal: str = ""
    signal_detail: Optional[str] = None

    # Location
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    # Meta
    schema_id: str = "csv-upload"
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DemandRecord:
    """Demand record for matching - matches TypeScript DemandRecord"""
    domain: str
    company: str
    contact: str
    email: str
    title: str
    industry: str
    signals: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SupplyRecord:
    """Supply record for matching - matches TypeScript SupplyRecord"""
    domain: str
    company: str
    contact: str
    email: str
    title: str
    industry: str
    capability: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """Edge/connection between demand and supply"""
    evidence: str
    confidence: float
    signals: List[str] = field(default_factory=list)


@dataclass
class NeedProfile:
    """Need profile extracted from demand - matches TypeScript NeedProfile"""
    category: str  # engineering, sales, marketing, biotech, healthcare, etc.
    specifics: List[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = 'none'


@dataclass
class CapabilityProfile:
    """Capability profile extracted from supply - matches TypeScript CapabilityProfile"""
    category: str  # recruiting, marketing, engineering, biotech_contact, etc.
    specifics: List[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = 'none'


@dataclass
class Match:
    """Match between demand and supply records"""
    demand: NormalizedRecord
    supply: NormalizedRecord
    score: float
    reasons: List[str] = field(default_factory=list)
    tier: Literal['strong', 'good', 'open'] = 'open'
    tier_reason: str = ""
    need_profile: Optional[NeedProfile] = None
    capability_profile: Optional[CapabilityProfile] = None
    buyer_seller_valid: Optional[bool] = None


@dataclass
class MatchingResult:
    """Result of matching operation"""
    demand_matches: List[Match]
    supply_aggregates: List[Dict[str, Any]]
    stats: Dict[str, Any]


@dataclass
class EnrichmentResult:
    """Result of enrichment operation"""
    action: str
    outcome: str
    email: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    verified: bool = False
    source: str = "none"
    inputs_present: Dict[str, bool] = field(default_factory=dict)
    providers_attempted: List[str] = field(default_factory=list)
    provider_results: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class GeneratedIntros:
    """Generated introduction emails"""
    demand_intro: str
    supply_intro: str
    value_props: Dict[str, str] = field(default_factory=dict)
    source: str = 'ai'  # 'ai' or 'fallback'
    error: Optional[str] = None  # Error message if fallback was used
