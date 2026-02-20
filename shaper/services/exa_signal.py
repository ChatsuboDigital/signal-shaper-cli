"""
Exa-Powered Signal Generation Service

Uses Exa web search API to research companies, then AI to synthesize
findings into concise WHY NOW signals (<30 words).

Demand signals: Hiring activity, funding, expansion — the timing trigger
Supply signals: What they do + why they need intros/deal flow
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from ..banner import console

# Optional imports
try:
    from exa_py import Exa
    HAS_EXA = True
except ImportError:
    HAS_EXA = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# =============================================================================
# PROMPTS
# =============================================================================

DEMAND_SIGNAL_PROMPT = """Extract a WHY NOW timing trigger for a cold intro email.

Company: {company_name}
Domain: {domain}
{context_line}
Recent activity found online:
{research}

YOUR JOB: Find the single strongest timing trigger from the research above.

PRIORITY ORDER (use the first one you find):
1. Hiring specific roles → "Hiring: VP of Sales" or "Posted 3 Clinical Research Associates"
2. Funding raised → "Just raised $10M Series A" or "Closed $50M PE fund"
3. Expansion / new market → "Opening London office" or "Expanding into biotech"
4. Leadership change → "New CTO joined from Stripe" or "New Managing Partner from Goldman"
5. Product launch / growth signal → "Just launched enterprise tier" or "New fund vehicle launched"
6. Partnership / contract win → "Signed enterprise contract with Fortune 500" or "New partnership with AWS"

FORMAT:
- Under 30 words, one line
- Start with the trigger type when possible: "Hiring:", "Raised:", "Expanding:", "Partnership:"
- Be specific — real titles, real numbers, real details from the research
- If nothing concrete found, return exactly: NONE

CRITICAL — INCLUDE THE DEPARTMENT/FUNCTION KEYWORD:
The signal is used by a matching system that detects these categories:
  engineering: engineer, developer, software, tech, CTO, SWE, full-stack, backend
  sales: sales, account executive, revenue, SDR, BDR, account manager, AE, VP Sales
  marketing: marketing, growth, brand, content, SEO, CMO, demand gen, performance
  finance: finance, CFO, accounting, controller, wealth, portfolio manager, FP&A
  operations: operations, ops, COO, supply chain, logistics, procurement
  recruiting: recruiter, talent, HR, hiring manager, staffing, TA, CHRO, people ops
  clinical/biotech: clinical, research, scientist, biotech, pharma, lab, medical, CRA, CRO
  investment/PE: analyst, associate, principal, partner, fund, portfolio, PE, VC, deal flow
  legal/compliance: general counsel, compliance, legal, attorney, regulatory

Always include the specific role title with its function keyword.
"Hiring: 3 Sales Engineers" is better than "Hiring: 3 new team members"
"Hiring: Senior Clinical Research Associate" is better than "Growing science team"
"Hiring: Investment Analyst" is better than "Expanding the team"

Signal:"""

CONTEXT_PROMPT = """Write a 1-2 sentence description of what this company does.

Company: {company_name}
Domain: {domain}
Info found online:
{research}

YOUR JOB: Describe what this company does in plain, factual language.

RULES:
- 1-2 sentences only
- Mention their core service/product and who they serve
- No marketing fluff or superlatives
- If you cannot determine what they do, return exactly: NONE

Description:"""

SUPPLY_SIGNAL_PROMPT = """Write a one-line signal for a service provider explaining what they do and why they need intros.

Company: {company_name}
Domain: {domain}
{context_line}
{research_line}

YOUR JOB: Describe what this company does + why connecting them to companies makes sense.

FORMAT: "[Capability type] for [industry/vertical], needs [what they need]"

GOOD EXAMPLES (notice the capability keywords — cover many industries):
- "Recruiting sales talent for SaaS companies, needs deal flow"
- "IT staffing for healthcare orgs, needs qualified buyer intros"
- "Clinical recruitment for biotech firms, needs pharma hiring leads"
- "Wealth management advisory for HNW clients, needs referral intros"
- "PE deal sourcing for middle-market buyouts, needs portfolio pipeline"
- "Software development agency for fintech startups, needs pipeline"
- "Fractional CFO consulting for Series A startups, needs warm intros"
- "Marketing agency for e-commerce brands, needs enterprise leads"
- "Lab equipment supplier for biotech/pharma, needs procurement contacts"
- "Executive search for financial services, needs retained search mandates"

BAD EXAMPLES (too vague — no matchable keywords):
- "Provides business solutions, needs clients" ← what solutions?
- "Technology company, needs growth" ← say what they actually do
- "Staffing company for growing businesses" ← what kind of staffing? what businesses?
- "Helps companies scale" ← how? recruiting? consulting? development?
- "Investment firm" ← what kind? PE, VC, wealth? what do they need?

If the research includes evidence of specific clients or industries served, reference them directly.
Example: if research shows healthcare clients → "Recruiting clinical talent for healthcare orgs" not "Recruiting talent for companies"

CRITICAL — USE THESE CAPABILITY KEYWORDS so the matching system can connect them:
  recruiting/staffing/talent/placement/headhunting/executive search → hiring-related services
  development/engineering/software/dev agency/SWE/full-stack → tech services
  marketing/advertising/creative/content/SEO/growth/demand gen → marketing services
  consulting/advisory/fractional/interim → consulting services
  finance/accounting/bookkeeping/wealth management/FP&A → finance services
  clinical/research/lab/biotech/pharma/CRO → life sciences services
  investment/PE/VC/fund/deal sourcing/capital/M&A → investment services
  legal/compliance/regulatory → legal services

RULES:
- MUST include at least one capability keyword from the list above
- Be specific about their vertical/niche (SaaS, fintech, healthcare, biotech, PE, wealth, etc.)
- Be specific about what they do (recruit, staff, build, consult, invest, advise, etc.)
- Under 30 words
- If you can't determine what they do, return exactly: NONE

Signal:"""


class ExaSignalGenerator:
    """
    Generate signals by researching companies with Exa and synthesizing with AI.

    Strategy:
    - DEMAND: Always search Exa for recent hiring/funding/news activity.
      Pass company_description as context to help AI understand the company.
    - SUPPLY: Use company_description if available (no Exa needed).
      Only search Exa if we don't know what the company does.
    """

    def __init__(
        self,
        exa_api_key: str,
        ai_provider: str = 'openai',
        ai_api_key: str = '',
        ai_model: Optional[str] = None,
    ):
        if not HAS_EXA:
            raise ImportError("exa_py package required. Install with: pip install exa-py")

        self.exa = Exa(api_key=exa_api_key)
        self.ai_provider = ai_provider
        self.ai_api_key = ai_api_key
        self.ai_model = ai_model

        # Initialize AI client once (connection reuse across all calls)
        self._ai_client = None
        if ai_provider == 'openai' and HAS_OPENAI and ai_api_key:
            self._ai_client = openai.OpenAI(api_key=ai_api_key)
        elif ai_provider == 'anthropic' and HAS_ANTHROPIC and ai_api_key:
            self._ai_client = Anthropic(api_key=ai_api_key)

        # Stats
        self.search_count = 0
        self.ai_call_count = 0
        self.cache_hits = 0
        self.signals_generated = 0
        self.skipped_no_data = 0
        self.failed = 0

        # Error tracking — distinct errors collected during enrichment
        self._errors: List[str] = []

        # Cache by domain
        self.cache: Dict[str, str] = {}

    @classmethod
    def from_env(cls) -> 'ExaSignalGenerator':
        """Create generator from environment variables."""
        exa_key = os.getenv('EXA_API_KEY', '')
        if not exa_key:
            raise ValueError("EXA_API_KEY required. Set it in .env file.")

        ai_provider = os.getenv('AI_PROVIDER', 'openai')

        if ai_provider == 'openai':
            ai_key = os.getenv('OPENAI_API_KEY', '')
            ai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        elif ai_provider == 'anthropic':
            ai_key = os.getenv('ANTHROPIC_API_KEY', '')
            ai_model = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
        else:
            ai_key = ''
            ai_model = None

        return cls(
            exa_api_key=exa_key,
            ai_provider=ai_provider,
            ai_api_key=ai_key,
            ai_model=ai_model,
        )

    # =========================================================================
    # EXA SEARCH
    # =========================================================================

    def _search_demand(self, domain: str, company_name: str) -> str:
        """
        Search for demand signals: hiring, funding, expansion.

        Two targeted queries with highlights:
          1. Hiring — job boards, highlights focused on role titles + departments
          2. Funding/news — news category, highlights focused on amounts + rounds
        Falls back to a general query if both return nothing.
        """
        search_name = company_name or domain
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        parts = []

        # Query 1 — Hiring signals (job boards, keyword search, fresh content)
        try:
            r = self.exa.search_and_contents(
                f'"{search_name}" hiring OR "open role" OR "job opening" OR "we\'re hiring" OR "now hiring"',
                num_results=4,
                start_published_date=start_date,
                include_domains=["builtin.com", "greenhouse.io", "lever.co", "jobs.ashbyhq.com", "wellfound.com"],
                highlights={"query": "job title role department function team size headcount", "maxCharacters": 300},
                type="keyword",
                livecrawl="preferred",
            )
            self.search_count += 1
            parts.append(self._format_results(r))
        except Exception:
            pass

        # Query 2 — Funding / news (news category, neural search)
        try:
            r = self.exa.search_and_contents(
                f'"{search_name}" raised OR funding OR "series A" OR "series B" OR expansion OR acquisition OR partnership',
                num_results=4,
                start_published_date=start_date,
                include_domains=["techcrunch.com", "crunchbase.com", "businesswire.com", "prnewswire.com", "reuters.com", "bloomberg.com"],
                highlights={"query": "funding amount raised series round investment expansion", "maxCharacters": 300},
                category="news",
                type="auto",
            )
            self.search_count += 1
            parts.append(self._format_results(r))
        except Exception:
            pass

        combined = '\n'.join(p for p in parts if p)

        # Fallback — general query if both targeted searches returned nothing
        if not combined:
            try:
                r = self.exa.search_and_contents(
                    f'"{search_name}" hiring OR funding OR raised OR expanding',
                    num_results=5,
                    start_published_date=start_date,
                    highlights={"query": "hiring role funding raised expansion", "maxCharacters": 300},
                    type="auto",
                )
                self.search_count += 1
                combined = self._format_results(r)
            except Exception as e:
                self.failed += 1
                err = f"Exa demand error for '{search_name}': {type(e).__name__}: {e}"
                if err not in self._errors:
                    self._errors.append(err)

        return combined

    def _search_supply(self, domain: str, company_name: str) -> str:
        """
        Search for supply info: what the company does, who they serve.

        Two targeted queries with highlights:
          1. Company domain — company category, highlights on services + expertise
          2. Client evidence — neural search for case studies, trusted-by mentions
        Falls back to a general query if neither returns anything.
        """
        search_name = company_name or domain
        parts = []

        # Primary: company's own domain (company category for best coverage)
        if domain:
            try:
                results = self.exa.search_and_contents(
                    f"{company_name or domain} services expertise",
                    num_results=3,
                    include_domains=[domain],
                    highlights={"query": "services clients industries expertise capabilities vertical niche", "maxCharacters": 350},
                    category="company",
                    type="auto",
                )
                self.search_count += 1
                text = self._format_results(results)
                if text:
                    parts.append(text)
            except Exception:
                pass

        # Secondary: client/vertical evidence (neural — finds semantically similar content)
        try:
            results = self.exa.search_and_contents(
                f'"{search_name}" client OR "case study" OR "we help" OR "trusted by" OR "works with"',
                num_results=3,
                highlights={"query": "client industry vertical customer sector we help", "maxCharacters": 300},
                type="neural",
            )
            self.search_count += 1
            text = self._format_results(results)
            if text:
                parts.append(text)
        except Exception:
            pass

        # Fallback: general search if neither returned results
        if not parts:
            try:
                results = self.exa.search_and_contents(
                    f'"{search_name}" specializes OR "we help" OR "our clients" OR "our work"',
                    num_results=3,
                    highlights={"query": "specializes services clients expertise vertical", "maxCharacters": 300},
                    type="neural",
                )
                self.search_count += 1
                parts.append(self._format_results(results))
            except Exception as e:
                self.failed += 1
                err = f"Exa supply error for '{search_name}': {type(e).__name__}: {e}"
                if err not in self._errors:
                    self._errors.append(err)

        return '\n'.join(p for p in parts if p)

    def _format_results(self, results) -> str:
        """Format Exa results into text for AI prompt.

        Prefers highlights (targeted excerpts) over full text — more relevant
        and token-efficient. Falls back to truncated text if highlights absent.
        """
        texts = []
        for r in results.results:
            title = getattr(r, 'title', '') or ''
            highlights = getattr(r, 'highlights', None) or []
            text = getattr(r, 'text', '') or ''
            published = getattr(r, 'published_date', '') or ''

            date_tag = f" [{published[:10]}]" if published else ''
            content = ' | '.join(h for h in highlights if h) if highlights else text[:300]

            if title or content:
                line = f"- {title}{date_tag}"
                if content:
                    line += f": {content}"
                texts.append(line)

        return '\n'.join(texts) if texts else ''

    # =========================================================================
    # AI SYNTHESIS
    # =========================================================================

    def _call_ai(self, prompt: str, max_tokens: int = 120) -> str:
        """Call AI provider to synthesize signal/context from research."""
        if not self._ai_client:
            return ''
        try:
            if self.ai_provider == 'openai':
                response = self._ai_client.chat.completions.create(
                    model=self.ai_model or 'gpt-4o-mini',
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.3,
                    max_tokens=max_tokens,
                )
                self.ai_call_count += 1
                return (response.choices[0].message.content or '').strip()

            elif self.ai_provider == 'anthropic':
                response = self._ai_client.messages.create(
                    model=self.ai_model or 'claude-3-haiku-20240307',
                    max_tokens=max_tokens,
                    temperature=0.3,
                    messages=[{'role': 'user', 'content': prompt}],
                )
                self.ai_call_count += 1
                return response.content[0].text.strip() if response.content else ''

            return ''

        except Exception as e:
            err = f"AI call error ({self.ai_provider}): {type(e).__name__}: {e}"
            if err not in self._errors:
                self._errors.append(err)
            return ''

    def _clean_signal(self, raw: str) -> Optional[str]:
        """Clean AI output into usable signal. Returns None if unusable."""
        if not raw:
            return None

        signal = raw.strip().strip('"\'').strip()

        # AI returned "NONE" — means no clear signal found
        if signal.upper() in ('NONE', 'N/A', 'EMPTY', '""', "''"):
            return None

        # Remove "Signal:" prefix if AI echoed it
        if signal.lower().startswith('signal:'):
            signal = signal[7:].strip()

        # Remove trailing period
        if signal.endswith('.'):
            signal = signal[:-1]

        # Sanity check: too short or too long
        if len(signal) < 5 or len(signal) > 200:
            return None

        return signal

    # =========================================================================
    # MAIN GENERATION
    # =========================================================================

    def generate_signal(
        self,
        domain: str,
        company_name: str,
        data_type: str = 'demand',
        company_description: str = '',
    ) -> Optional[str]:
        """
        Generate a signal for a single company.

        For DEMAND: Searches Exa for hiring/funding activity, uses AI to extract trigger.
        For SUPPLY: Uses company_description if available, searches Exa only if needed.
        """
        if not domain and not company_name:
            self.skipped_no_data += 1
            return None

        # Cache check
        cache_key = f"{data_type}:{(domain or company_name).lower().strip()}"
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]

        # Context line for AI prompt (pass what we know about the company)
        context_line = f"What they do: {company_description[:300]}" if company_description else ""

        if data_type == 'demand':
            # DEMAND: Always search Exa — we need RECENT activity
            research = self._search_demand(domain, company_name)
            if not research:
                return None

            prompt = DEMAND_SIGNAL_PROMPT.format(
                company_name=company_name or domain,
                domain=domain or '',
                context_line=context_line,
                research=research,
            )

        else:
            # SUPPLY: Use description if available — no Exa needed when we know what they do
            if company_description:
                # Description is enough — synthesize from context_line alone
                research_line = ""
            else:
                # No description — must search Exa
                research = self._search_supply(domain, company_name)
                if not research:
                    return None
                research_line = f"Info found online:\n{research}"

            prompt = SUPPLY_SIGNAL_PROMPT.format(
                company_name=company_name or domain,
                domain=domain or '',
                context_line=context_line,
                research_line=research_line,
            )

        # AI synthesis
        raw = self._call_ai(prompt)
        signal = self._clean_signal(raw)

        if signal:
            self.cache[cache_key] = signal
            self.signals_generated += 1
            return signal

        return None

    def enrich_batch(
        self,
        records: List[Dict[str, str]],
        data_type: str = 'demand',
        overwrite_signal: bool = False,
        generate_signal: bool = True,
        generate_context: bool = True,
        show_progress: bool = True,
    ) -> List[Dict[str, str]]:
        """
        Enrich records with signals and context in a single efficient Exa pass.

        For each company:
          - SUPPLY: one Exa search feeds both signal and context AI calls (run in parallel).
          - DEMAND: two parallel Exa searches (hiring activity + company info) feed
                    separate AI calls for signal and context (also run in parallel).

        Records that already have both signal and company_description are skipped entirely.
        """
        import concurrent.futures as cf
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

        raw_results: list = []
        signals_out = 0
        contexts_out = 0

        def process_record(idx_record):
            idx, record = idx_record
            domain = record.get('domain', '')
            company_name = record.get('company', '') or record.get('company_name', '')

            if not domain and not company_name:
                return idx, record, False, False

            need_signal = generate_signal and (overwrite_signal or not record.get('signal'))
            need_context = generate_context and not record.get('company_description')

            if not need_signal and not need_context:
                return idx, record, False, False

            existing_desc = record.get('company_description', '')
            context_line = f"What they do: {existing_desc[:300]}" if existing_desc else ""

            # ── Exa research ───────────────────────────────────────────────
            if data_type == 'supply':
                # Supply: one search — company info for both signal and context.
                # Skip if we already have a description and don't need context.
                if existing_desc and not need_context:
                    supply_research = ''
                else:
                    supply_research = self._search_supply(domain, company_name)
                demand_research = ''
            else:
                # Demand: one search — hiring/funding activity for both signal and context.
                demand_research = self._search_demand(domain, company_name) if (need_signal or need_context) else ''
                supply_research = ''

            # ── Build AI prompts ───────────────────────────────────────────
            prompts: Dict[str, str] = {}

            if need_signal:
                if data_type == 'supply' and (supply_research or existing_desc):
                    # Use Exa results if available, fall back to context_line alone
                    research_line = f"Info found online:\n{supply_research}" if supply_research else ""
                    prompts['signal'] = SUPPLY_SIGNAL_PROMPT.format(
                        company_name=company_name or domain,
                        domain=domain or '',
                        context_line=context_line,
                        research_line=research_line,
                    )
                elif data_type == 'demand' and demand_research:
                    prompts['signal'] = DEMAND_SIGNAL_PROMPT.format(
                        company_name=company_name or domain,
                        domain=domain or '',
                        context_line=context_line,
                        research=demand_research,
                    )

            # Context uses the research appropriate for each data type — no cross-pollination
            context_research = demand_research if data_type == 'demand' else supply_research
            if need_context and context_research:
                prompts['context'] = CONTEXT_PROMPT.format(
                    company_name=company_name or domain,
                    domain=domain or '',
                    research=context_research,
                )

            if not prompts:
                return idx, record, False, False

            # ── Parallel AI calls ──────────────────────────────────────────
            # Context gets more tokens (2 sentences) vs signal (1 line <30 words)
            sig_ok = False
            ctx_ok = False
            with cf.ThreadPoolExecutor(max_workers=len(prompts)) as ex:
                ai_futures = {
                    kind: ex.submit(self._call_ai, prompt, 150 if kind == 'context' else 80)
                    for kind, prompt in prompts.items()
                }
                for kind, future in ai_futures.items():
                    raw = future.result()
                    if kind == 'signal':
                        signal = self._clean_signal(raw)
                        if signal:
                            record['signal'] = signal
                            sig_ok = True
                    elif kind == 'context':
                        if raw and raw.strip().upper() not in ('NONE', 'N/A', ''):
                            desc = raw.strip().strip('"\'')
                            if 10 <= len(desc) <= 500:
                                record['company_description'] = desc
                                ctx_ok = True

            return idx, record, sig_ok, ctx_ok

        indexed_records = list(enumerate(records))

        total = len(records)

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[cyan]{task.completed}/{task.total}[/cyan]"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Enriching with Exa...", total=total)

                with cf.ThreadPoolExecutor(max_workers=10) as executor:
                    future_map = {
                        executor.submit(process_record, item): item
                        for item in indexed_records
                    }
                    for future in cf.as_completed(future_map):
                        idx, record, sig_ok, ctx_ok = future.result()
                        company = (
                            record.get('company', '')
                            or record.get('company_name', '')
                            or record.get('domain', '')
                            or ''
                        )
                        if sig_ok:
                            signals_out += 1
                            self.signals_generated += 1
                        if ctx_ok:
                            contexts_out += 1
                        raw_results.append((idx, record))

                        result_parts = []
                        if sig_ok: result_parts.append("signal ☉")
                        if ctx_ok: result_parts.append("context ☉")
                        result_str = "  " + "  ".join(result_parts) if result_parts else ""
                        desc = f"[cyan]{company[:30]}[/cyan][dim]{result_str}[/dim]" if company else "[cyan]Enriching...[/cyan]"
                        progress.update(task, description=desc, advance=1)
        else:
            with cf.ThreadPoolExecutor(max_workers=10) as executor:
                future_map = {
                    executor.submit(process_record, item): item
                    for item in indexed_records
                }
                for future in cf.as_completed(future_map):
                    idx, record, sig_ok, ctx_ok = future.result()
                    if sig_ok:
                        signals_out += 1
                        self.signals_generated += 1
                    if ctx_ok:
                        contexts_out += 1
                    raw_results.append((idx, record))

        raw_results.sort(key=lambda x: x[0])
        ordered_records = [r for _, r in raw_results]

        sig_pct  = f"{signals_out  / total * 100:.0f}%" if total else "0%"
        ctx_pct  = f"{contexts_out / total * 100:.0f}%" if total else "0%"
        console.print(
            f"[green]☉ Signals: {signals_out}/{total} ({sig_pct})"
            f"  ·  Context: {contexts_out}/{total} ({ctx_pct})[/green]"
        )

        return ordered_records

    def get_stats(self) -> Dict[str, int]:
        """Get generation statistics."""
        return {
            'exa_searches': self.search_count,
            'ai_calls': self.ai_call_count,
            'cache_hits': self.cache_hits,
            'signals_generated': self.signals_generated,
            'skipped_no_data': self.skipped_no_data,
            'failed': self.failed,
        }

    def get_errors(self) -> List[str]:
        """Return distinct errors collected during enrichment."""
        return list(self._errors)
