"""
Buyer-Seller type extraction and validation.

Port of connector-os/src/matching/buyerSellerTypes.ts

SUPPLY TRUTH CONSTRAINT:
- Matching = buyer-seller overlap, NOT just industry overlap
- If supply doesn't explicitly sell to demand type → filtered out
- Custom mode bypasses validation (user responsibility)
"""

from typing import Dict, List, Optional, Tuple, Any


# Token dictionaries per connector mode
_MODE_TOKENS: Dict[str, Dict[str, Any]] = {
    'recruiting': {
        'supply_buyer': [
            'hiring', 'talent acquisition', 'headcount', 'open roles', 'recruiting',
            'staffing', 'placement', 'executive search', 'hr', 'human resources',
        ],
        'demand_type': [
            'hiring', 'growing team', 'scaling', 'open positions', 'headcount',
            'talent', 'recruiting', 'job posting',
        ],
        'disallowed_peers': [
            'staffing agency', 'recruitment firm', 'headhunter', 'talent agency',
        ],
        'default_buyer': 'hiring_teams',
        'default_demand': 'hiring_company',
    },
    'biotech_licensing': {
        'supply_buyer': [
            'pharma', 'biotech', 'licensing', 'bd', 'business development',
            'partnership', 'clinical', 'pipeline', 'therapeutic', 'molecule',
        ],
        'demand_type': [
            'biotech', 'pharma', 'clinical stage', 'therapeutics', 'drug',
            'molecule', 'pipeline', 'fda', 'trial',
        ],
        'disallowed_peers': ['cro', 'contract research', 'clinical trial services'],
        'default_buyer': 'pharma_bd_teams',
        'default_demand': 'biotech_company',
    },
    'wealth_management': {
        'supply_buyer': [
            'hnw', 'high net worth', 'uhnw', 'family office', 'wealth',
            'private client', 'affluent', 'investor', 'estate',
        ],
        'demand_type': [
            'ria', 'wealth', 'advisory', 'financial planning', 'fiduciary',
            'cfp', 'family office', 'private wealth',
        ],
        'disallowed_peers': [
            'wealth advisor', 'ria', 'financial planner', 'cfp', 'wealth management firm',
        ],
        'default_buyer': 'hnw_individuals',
        'default_demand': 'wealth_advisory_firm',
    },
    'real_estate_capital': {
        'supply_buyer': [
            'developer', 'sponsor', 'operator', 'gp', 'real estate', 'property',
            'cre', 'commercial', 'multifamily', 'acquisition',
        ],
        'demand_type': [
            'developer', 'sponsor', 'real estate', 'property', 'cre',
            'commercial', 'multifamily', 'development',
        ],
        'disallowed_peers': ['lender', 'debt fund', 'capital provider', 'equity fund'],
        'default_buyer': 're_developers',
        'default_demand': 're_sponsor',
    },
    'logistics': {
        'supply_buyer': [
            'shipper', 'manufacturer', 'retailer', 'ecommerce', 'brand',
            'fulfillment', 'warehouse', 'distribution',
        ],
        'demand_type': [
            'shipper', 'logistics', 'supply chain', '3pl', 'freight',
            'warehouse', 'fulfillment', 'distribution',
        ],
        'disallowed_peers': ['3pl', 'freight broker', 'logistics provider', 'warehouse operator'],
        'default_buyer': 'shippers',
        'default_demand': 'logistics_company',
    },
    'crypto': {
        'supply_buyer': [
            'product', 'engineering', 'fintech', 'platform', 'exchange',
            'defi', 'protocol', 'web3', 'blockchain', 'crypto', 'payments',
            'compliance', 'kyc', 'aml',
        ],
        'demand_type': [
            'crypto', 'blockchain', 'web3', 'defi', 'protocol', 'exchange',
            'token', 'nft', 'dao', 'fintech platform',
        ],
        'disallowed_peers': [
            'wealth', 'ria', 'financial advisor', 'wealth management',
            'family office', 'private wealth', 'investment advisor',
        ],
        'default_buyer': 'crypto_product_teams',
        'default_demand': 'crypto_platform',
    },
    'enterprise_partnerships': {
        'supply_buyer': [
            'enterprise', 'b2b', 'saas', 'platform', 'integration',
            'partnership', 'vendor', 'solution', 'software',
        ],
        'demand_type': [
            'enterprise', 'b2b', 'saas', 'platform', 'software', 'solution', 'vendor',
        ],
        'disallowed_peers': ['consultant', 'agency', 'implementation partner'],
        'default_buyer': 'enterprise_teams',
        'default_demand': 'enterprise_company',
    },
    'custom': {
        'supply_buyer': [],
        'demand_type': [],
        'disallowed_peers': [],
        'default_buyer': 'general',
        'default_demand': 'company',
    },
}


def _build_text(record, *fields: str) -> str:
    """Build lowercase searchable text from record fields."""
    parts = []
    for field in fields:
        val = getattr(record, field, '') or ''
        if isinstance(val, list):
            parts.append(' '.join(str(v) for v in val))
        elif val:
            parts.append(str(val))
    return ' '.join(parts).lower()


def _confidence(matched: List[str]) -> str:
    if len(matched) >= 3:
        return 'high'
    if len(matched) >= 1:
        return 'medium'
    return 'low'


def _infer_buyer_type(tokens: List[str], mode: str, default: str) -> str:
    t = set(tokens)
    if mode == 'crypto':
        if 'product' in t or 'engineering' in t:
            return 'crypto_product_teams'
        if 'compliance' in t or 'kyc' in t or 'aml' in t:
            return 'compliance_teams'
        if 'fintech' in t or 'platform' in t:
            return 'fintech_platforms'
    elif mode == 'wealth_management':
        if 'hnw' in t or 'high net worth' in t or 'uhnw' in t:
            return 'hnw_individuals'
        if 'family office' in t:
            return 'family_offices'
    elif mode == 'recruiting':
        if 'executive search' in t:
            return 'executive_hiring'
        if 'talent acquisition' in t:
            return 'talent_teams'
    elif mode == 'biotech_licensing':
        if 'bd' in t or 'business development' in t:
            return 'pharma_bd_teams'
        if 'licensing' in t:
            return 'licensing_teams'
    return default


def _infer_demand_type(tokens: List[str], mode: str, default: str) -> str:
    t = set(tokens)
    if mode == 'crypto':
        if 'exchange' in t:
            return 'crypto_exchange'
        if 'defi' in t or 'protocol' in t:
            return 'defi_protocol'
        if 'nft' in t:
            return 'nft_platform'
    elif mode == 'wealth_management':
        if 'ria' in t:
            return 'ria_firm'
        if 'family office' in t:
            return 'family_office'
    elif mode == 'recruiting':
        if 'scaling' in t or 'growing team' in t:
            return 'scaling_company'
    return default


def _check_mode_overlap(supply_tokens: List[str], demand_tokens: List[str], mode: str) -> bool:
    """Mode-specific cross-contamination rules."""
    if mode == 'crypto':
        wealth_words = {'wealth', 'ria', 'advisor', 'family office', 'private wealth'}
        if any(t in wealth_words for t in supply_tokens):
            return False
    if mode == 'wealth_management':
        platform_words = {'crypto', 'blockchain', 'fintech platform', 'exchange'}
        if any(t in platform_words for t in demand_tokens):
            return False
    return True


def validate_match(supply_record, demand_record, mode: str) -> Tuple[bool, Optional[str]]:
    """
    Validate buyer-seller overlap for a supply-demand pair.

    Returns (valid, reason):
      (True, None)                     — valid match
      (False, 'BUYER_SELLER_MISMATCH') — supply doesn't sell to this demand type

    Rules:
      1. Custom mode always passes (user-defined data, user responsibility)
      2. Supply is a disallowed peer type → invalid
      3. Both low confidence → allow (insufficient signal, don't block)
      4. Mode-specific cross-contamination check
    """
    if mode == 'custom' or mode not in _MODE_TOKENS:
        return True, None

    tokens = _MODE_TOKENS[mode]

    supply_text = _build_text(supply_record, 'company_description', 'industry', 'title')
    demand_text = _build_text(demand_record, 'company_description', 'industry', 'signal')

    # Rule 1: Disallowed peer types on supply side
    if any(peer in supply_text for peer in tokens['disallowed_peers']):
        return False, 'BUYER_SELLER_MISMATCH'

    # Rule 2: Extract buyer/demand tokens and confidence
    supply_matched = [t for t in tokens['supply_buyer'] if t in supply_text]
    demand_matched = [t for t in tokens['demand_type'] if t in demand_text]

    # Both low confidence → insufficient signal, allow
    if _confidence(supply_matched) == 'low' and _confidence(demand_matched) == 'low':
        return True, None

    # Rule 3: Mode-specific cross-contamination
    if not _check_mode_overlap(supply_matched, demand_matched, mode):
        return False, 'BUYER_SELLER_MISMATCH'

    return True, None
