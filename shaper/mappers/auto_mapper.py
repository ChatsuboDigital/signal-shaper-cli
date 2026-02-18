"""
Auto field mapper

Automatically detects and maps common field names from various data sources
to the NormalizedRecord schema format.
"""

from typing import Dict, List, Optional
from core.models import FieldMapping


# Field detection patterns (ordered by priority)
# Comprehensive patterns to handle scrapes from multiple sources
FIELD_PATTERNS = {
    'full_name': [
        # Exact matches first
        'fullName', 'full_name', 'name', 'contactName', 'contact_name',
        'Full Name', 'Name', 'Contact Name', 'person_name', 'personName',
        # Common variations
        'contact', 'Contact', 'person', 'Person', 'individual', 'Individual',
        'lead_name', 'leadName', 'prospect_name', 'prospectName',
        # Scraper-specific
        'scraped_name', 'person_full_name', 'full_contact_name',
        'owner', 'Owner', 'founder', 'Founder', 'ceo', 'CEO'
    ],
    'company_name': [
        # Exact matches first
        'companyName', 'company_name', 'company', 'organization', 'org',
        'Company', 'Company Name', 'Organization', 'companyname',
        # Common variations
        'employer', 'business_name', 'businessName', 'business', 'Business',
        'firm', 'Firm', 'corporation', 'Corporation', 'entity', 'Entity',
        # Scraper-specific
        'company_legal_name', 'legal_name', 'organization_name',
        'account', 'Account', 'client', 'Client', 'customer', 'Customer',
        'brand', 'Brand', 'venture', 'Venture', 'startup', 'Startup'
    ],
    'domain': [
        # Exact matches first
        'domain', 'website', 'url', 'companyDomain', 'company_domain',
        'Domain', 'Website', 'URL', 'company_website', 'companyWebsite',
        # Common variations
        'web', 'site', 'companyUrl', 'company_url', 'web_url', 'webUrl',
        'homepage', 'Homepage', 'site_url', 'siteUrl', 'web_address',
        # Scraper-specific
        'domain_name', 'domainName', 'company_site', 'companySite',
        'website_url', 'websiteUrl', 'web_domain', 'webDomain',
        'base_domain', 'baseDomain', 'root_domain', 'rootDomain',
        'link', 'Link', 'uri', 'URI'
    ],
    'email': [
        # Exact matches first
        'email', 'emailAddress', 'email_address', 'Email', 'Email Address',
        'e-mail', 'e_mail', 'mail', 'contact_email', 'contactEmail',
        # Common variations
        'work_email', 'workEmail', 'business_email', 'businessEmail',
        'corporate_email', 'corporateEmail', 'professional_email',
        # Scraper-specific
        'email_scraped', 'scraped_email', 'verified_email', 'verifiedEmail',
        'primary_email', 'primaryEmail', 'contact_mail', 'contactMail',
        'email_1', 'email1', 'Email1', 'email_primary'
    ],
    'signal': [
        # Explicit signal fields (HIGH PRIORITY)
        'signal', 'Signal', 'hiring_signal', 'hiringSignal', 'Hiring Signal',
        'trigger', 'Trigger', 'why_now', 'whyNow', 'Why Now',
        # Job posting fields — the ROLE being hired for (not the contact's own title)
        'job_posting', 'jobPosting', 'posting', 'Posting', 'opening', 'Opening',
        'vacancy', 'Vacancy', 'hiring_for', 'hiringFor',
        'open_role', 'openRole', 'open_position', 'openPosition',
        # Hiring intent
        'hiring_intent', 'hiringIntent',
        # NOTE: job_title, title, position, role are handled separately —
        # For DEMAND (job scrapes): these ARE the signal (the role being hired)
        # For SUPPLY: these are the contact's own title and should NOT be signal
        # See DEMAND_SIGNAL_PATTERNS below
    ],
    'company_description': [
        # Exact matches first
        'context', 'Context', 'companyDescription', 'company_description',
        'description', 'Description', 'about', 'About', 'Company Description',
        # Common variations
        'company_info', 'companyInfo', 'bio', 'company_bio', 'notes', 'Notes',
        'overview', 'Overview', 'summary', 'Summary', 'profile', 'Profile',
        # Scraper-specific
        'company_overview', 'companyOverview', 'about_company', 'aboutCompany',
        'business_description', 'businessDescription', 'company_summary',
        'companySummary', 'company_profile', 'companyProfile',
        'details', 'Details', 'info', 'Info', 'information', 'Information',
        'background', 'Background', 'company_background', 'companyBackground'
    ],
    # Additional signal patterns for DEMAND data only
    # For demand (job scrapes): job_title IS the signal — it's the role being hired
    # For supply: job_title is the contact's own title (e.g., "CEO") — NOT signal
    'signal_demand_extra': [
        'job_title', 'jobTitle', 'Job Title', 'title', 'Title',
        'position', 'Position', 'role', 'Role',
        'job', 'Job', 'current_position', 'currentPosition',
        'job_role', 'jobRole', 'Job Role',
    ],
}


class AutoMapper:
    """
    Automatically detect field mappings from source data.

    Example:
        mapper = AutoMapper(data_type='demand')
        mapping = mapper.auto_map(apify_record)
        print(f"Detected: {mapping.full_name} -> full_name")
    """

    def __init__(self, data_type: str = 'demand', custom_patterns: Optional[Dict[str, List[str]]] = None):
        """
        Initialize auto mapper.

        Args:
            data_type: 'demand' or 'supply' — affects signal detection behavior
            custom_patterns: Optional custom field patterns to merge with defaults
        """
        self.data_type = data_type
        self.patterns = {}

        # Copy base patterns (excluding the demand-only extras)
        for field, patterns in FIELD_PATTERNS.items():
            if field != 'signal_demand_extra':
                self.patterns[field] = list(patterns)

        # For demand data: append job_title/title/position to signal patterns
        # These are the roles being hired for — they ARE the demand signal
        if data_type == 'demand' and 'signal_demand_extra' in FIELD_PATTERNS:
            self.patterns['signal'] = self.patterns['signal'] + FIELD_PATTERNS['signal_demand_extra']

        if custom_patterns:
            for field, patterns in custom_patterns.items():
                if field in self.patterns:
                    # Prepend custom patterns (higher priority)
                    self.patterns[field] = patterns + self.patterns[field]
                else:
                    self.patterns[field] = patterns

    # Fields never auto-detected — always handled explicitly in Step 5
    SKIP_AUTO = {'signal', 'company_description'}

    def auto_map(self, sample_record: dict) -> FieldMapping:
        """
        Auto-detect field mappings from a sample record.

        Args:
            sample_record: A single record (dict) from the dataset

        Returns:
            FieldMapping with detected mappings (signal/context never auto-set)
        """
        mapping = FieldMapping()
        available_fields = set(sample_record.keys())

        # Try to map each target field — skip signal and context (handled in Step 5)
        for target_field, patterns in self.patterns.items():
            if target_field in self.SKIP_AUTO:
                continue
            for pattern in patterns:
                if pattern in available_fields:
                    setattr(mapping, target_field, pattern)
                    break

        return mapping

    def get_mapping_confidence(self, mapping: FieldMapping) -> float:
        """
        Calculate confidence score for the mapping (0.0 to 1.0).

        Based on:
        - Required fields mapped: +0.8 (domain + company_name, 0.4 each)
        - Optional fields mapped: +0.2 (full_name + email, proportional)

        Signal and context are excluded — always set explicitly in Step 5.

        Args:
            mapping: The field mapping to score

        Returns:
            Confidence score 0.0 to 1.0
        """
        score = 0.0

        # Required fields (80% of score) — need at least domain + company_name
        required = ['domain', 'company_name']
        for field in required:
            if getattr(mapping, field) is not None:
                score += 0.8 / len(required)

        # Optional fields (20% of score)
        optional = ['full_name', 'email']
        mapped_optional = sum(1 for field in optional if getattr(mapping, field) is not None)
        if optional:
            score += (mapped_optional / len(optional)) * 0.2

        return min(score, 1.0)

    def is_complete(self, mapping: FieldMapping) -> bool:
        """
        Check if mapping has all required fields.

        Args:
            mapping: Field mapping to check

        Returns:
            True if all required fields are mapped
        """
        return mapping.is_complete()

    def get_mapping_summary(self, mapping: FieldMapping) -> Dict[str, str]:
        """
        Get a summary of the field mapping.

        Args:
            mapping: Field mapping

        Returns:
            Dict of {target_field: source_field} for mapped fields
        """
        summary = {}
        for field in vars(mapping):
            source = getattr(mapping, field)
            if source is not None:
                summary[field] = source

        return summary
