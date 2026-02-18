"""
Exa-Powered Domain Resolution

Uses Exa's company search to find company domains from company names.
Lightweight — no AI needed, just Exa search + URL extraction.
"""

import os
from typing import Optional, Dict, List
from ..banner import console
from ..normalizers import normalize_domain

try:
    from exa_py import Exa
    HAS_EXA = True
except ImportError:
    HAS_EXA = False


class ExaDomainResolver:
    """
    Resolve company domains using Exa company search.

    Uses category="company" for entity-level matching.
    Extracts domain from the top result's URL.
    """

    def __init__(self, exa_api_key: str):
        if not HAS_EXA:
            raise ImportError("exa_py package required. Install with: pip install exa-py")

        self.exa = Exa(api_key=exa_api_key)

        # Stats
        self.resolved = 0
        self.failed = 0
        self.cache_hits = 0

        # Cache by company name
        self.cache: Dict[str, str] = {}

    @classmethod
    def from_env(cls) -> 'ExaDomainResolver':
        """Create resolver from environment variables."""
        exa_key = os.getenv('EXA_API_KEY', '')
        if not exa_key:
            raise ValueError("EXA_API_KEY required. Set it in .env file.")
        return cls(exa_api_key=exa_key)

    def resolve_domain(self, company_name: str, context: str = '') -> Optional[str]:
        """
        Find domain for a company name using Exa company search.

        Args:
            company_name: Company name to look up
            context: Extra context (location, industry, description) for disambiguation

        Returns:
            Normalized domain string (e.g., "acme.com") or None
        """
        if not company_name or not company_name.strip():
            return None

        # Cache check (include context in key for different disambiguation)
        cache_key = f"{company_name.lower().strip()}|{context.lower().strip()[:50]}"
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]

        # Build query: company name + context for disambiguation
        query = company_name.strip()
        if context:
            query = f"{query} {context.strip()}"

        try:
            results = self.exa.search(
                query=query,
                type="auto",
                category="company",
                num_results=1,
            )

            if results.results:
                url = results.results[0].url
                if url:
                    domain = normalize_domain(url)
                    if domain:
                        self.cache[cache_key] = domain
                        self.resolved += 1
                        return domain

            self.failed += 1
            return None

        except Exception:
            self.failed += 1
            return None

    def resolve_batch(
        self,
        records: List[Dict[str, str]],
        show_progress: bool = True,
    ) -> List[Dict[str, str]]:
        """
        Resolve missing domains for a batch of records.

        Only processes records where domain is empty but company_name exists.

        Args:
            records: List of processed record dicts
            show_progress: Show progress bar

        Returns:
            Records with domains filled where possible
        """
        import concurrent.futures
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

        # Find records that need domain resolution
        needs_domain = [
            (i, r) for i, r in enumerate(records)
            if not r.get('domain') and (r.get('company_name') or r.get('company'))
        ]

        if not needs_domain:
            console.print("[dim]No records need domain resolution[/dim]")
            return records

        def resolve_record(idx_record):
            idx, record = idx_record
            company = record.get('company_name') or record.get('company') or ''

            # Build context from raw data for better accuracy
            raw = record.get('_raw', {})
            context_parts = []

            # Location disambiguates (e.g., "Mercury San Francisco" vs "Mercury Detroit")
            for loc_field in ['jobLocation', 'job_location', 'location', 'Location', 'city', 'City']:
                loc = raw.get(loc_field, '')
                if loc:
                    context_parts.append(str(loc))
                    break

            # Industry/classification narrows the search
            for cls_field in ['classification', 'Classification', 'industry', 'Industry',
                              'subClassification', 'category', 'Category']:
                cls_val = raw.get(cls_field, '')
                if cls_val:
                    context_parts.append(str(cls_val))
                    break

            # Company description if available
            desc = record.get('company_description', '') or raw.get('advertiserDescription', '')
            if desc:
                context_parts.append(str(desc)[:100])

            context = ' '.join(context_parts)
            domain = self.resolve_domain(company, context=context)
            if domain:
                record['domain'] = domain
            return idx, record

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task(
                    "[cyan]Resolving domains with Exa...", total=len(needs_domain)
                )

                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {
                        executor.submit(resolve_record, item): item
                        for item in needs_domain
                    }

                    for future in concurrent.futures.as_completed(futures):
                        idx, record = future.result()
                        records[idx] = record
                        progress.update(task, advance=1)
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(resolve_record, item): item
                    for item in needs_domain
                }

                for future in concurrent.futures.as_completed(futures):
                    idx, record = future.result()
                    records[idx] = record

        return records

    def get_stats(self) -> Dict[str, int]:
        """Get resolution statistics."""
        return {
            'resolved': self.resolved,
            'failed': self.failed,
            'cache_hits': self.cache_hits,
        }
