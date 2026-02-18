```
███████╗██╗ ██████╗ ███╗   ██╗  █████╗ ██╗     ██╗███████╗
██╔════╝██║██╔════╝ ████╗  ██║ ██╔══██╗██║     ██║██╔════╝
███████╗██║██║  ███╗██╔██╗ ██║ ███████║██║     ██║███████╗
╚════██║██║██║   ██║██║╚██╗██║ ██╔══██║██║     ██║╚════██║
███████║██║╚██████╔╝██║ ╚████║ ██║  ██║███████╗██║███████║
╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝
```

**Signal intelligence and outreach data — from raw input to enriched, structured CSV.**

Signalis is a command-line framework for transforming scraped, exported, or sourced contact data into clean, normalized, signal-enriched records ready for any outreach or matching workflow. Think of it as [recon-ng](https://github.com/lanmaster53/recon-ng) or [theHarvester](https://github.com/laramies/theHarvester) — but purpose-built for signals and outreach intelligence rather than passive reconnaissance.

```
  Full Name  ·  Company Name  ·  Domain  ·  Email  ·  Context  ·  Signal
```

Shape raw contact data in the **Shaper**, then run the **Connector** to match supply to demand, enrich missing emails, generate AI intros, and send directly to campaign platforms.

---

## ⟶  Why Python

Most data tools for outreach are browser-based or SaaS. Signalis is neither. Python is the right environment for this kind of work:

- **Direct filesystem** — read/write CSVs, cache enrichments to disk, no storage hacks or upload limits
- **No memory ceiling** — process 100K records without a browser tab dying or a serverless function timing out
- **Concurrent API calls** — `requests` + `ThreadPoolExecutor` for Exa enrichment is cleaner than browser fetch + Promise.all, and saturates API rate limits properly
- **Scriptable and composable** — chain `signalis` in a cron job, CI pipeline, or shell script alongside other tools
- **Rich terminal UI** — progress bars, tables, panels, spinners — everything a web UI would show, without the complexity
- **Sequential by design** — the pipeline is inherently step-by-step (load → map → normalize → enrich → export), which maps perfectly to a CLI, not to a React render cycle

---

## ⟶  Install

### macOS / Linux

```bash
git clone https://github.com/ChatsuboDigital/signalis-framework.git
cd signalis-framework
chmod +x install.sh && ./install.sh
```

The installer creates a virtual environment, installs all dependencies, adds `signalis` to your PATH, and walks you through entering your API keys. After that, run from any directory — no activation required.

To also install Connector dependencies (matching, enrichment, intro generation, sending):

```bash
pip install -e ".[all]"
```

### Windows

```cmd
git clone https://github.com/ChatsuboDigital/signalis-framework.git
cd signalis-framework
install.bat
```

> Requires Python 3.9 or later. Get it from [python.org](https://www.python.org/downloads/). Check **Add Python to PATH** during installation.

---

## ☉  Launch

```bash
signalis
```

That is the entire invocation. The interactive mode guides you through each step. No flags, no path changes, no virtual environment activation.

To configure or update API keys at any time:

```bash
signalis setup
```

Or press **S** from the main menu to access settings inline.

To update to the latest version:

```bash
signalis update
```

Pulls the latest changes from GitHub and reinstalls any new dependencies automatically.

---

## ⚗  The Pipeline

Signalis runs a structured, inspectable pipeline on your data. Every step is visible, every decision is yours.

```
  Raw input (CSV or Apify dataset)
      │
      ├─ 1. Load          Read CSV or fetch from Apify by dataset ID
      ├─ 2. Map fields     Auto-detect columns or assign them manually
      ├─ 3. Preview        Inspect records before any processing
      ├─ 4. Normalize      Clean domains, names, emails, encoding issues
      ├─ 5. Signal & ctx   Set signals manually, map from a column, or use Exa
      ├─ 6. Enrich         Domain resolution → AI signals → company context
      └─ 7. Export         Timestamped CSV written to output/
```

### The 6-Column Output Schema

Every export has the same structure — regardless of what came in:

| Full Name | Company Name | Domain | Email | Context | Signal |
|-----------|--------------|--------|-------|---------|--------|
| Jane Smith | Acme Corp | acme.com | jane@acme.com | SaaS platform for HR teams | Hiring 3 sales engineers |
| John Doe | Bolt Inc | bolt.io | | Fast-growing logistics network | Raised $40M Series B |

Output files are saved to `output/` with timestamped names: `supply_2025-02-18_143022.csv`, `demand_2025-02-18_143045.csv`.

---

## ☾  Signals

A **signal** is a short statement — typically under 30 words — describing why a company or person is worth reaching out to *right now*. The timing trigger that makes an outreach relevant.

### Demand signals — companies buying or hiring

```
  Hiring 3 Senior Sales Engineers
  Raised $40M Series B — announced March 2025
  Opening London office, expanding into EMEA
  New CTO joined from Stripe last quarter
```

### Supply signals — people and companies offering services

```
  Recruiting senior sales talent for B2B SaaS companies, needs deal flow
  IT staffing for healthcare orgs, needs qualified buyer intros
  Fractional CFO consulting for Series A startups, needs warm intros
  Executive search for financial services, needs retained mandates
```

### Signal sources — mix and match

| Source | Behaviour |
|--------|-----------|
| **Column** | Map an existing column from your data as the signal field |
| **Global text** | A single signal applied to every record |
| **Signal prefix** | Text prepended to all signals — `"Hired: "` → `"Hired: 3 sales engineers"` |
| **Exa AI** | Exa researches each company; an AI model writes a specific signal per record |
| *(none)* | Signal column left blank — fill it downstream |

Column and global text are mutually exclusive. Exa is independent — it can fill blanks, override, or run alone. All combinations are supported and shown in a summary panel at the end of Step 5.

---

## ◈  Enrichment

The core pipeline runs without any API keys — normalization, mapping, and export work out of the box. Enrichment layers intelligence on top via external APIs.

### Exa — domain resolution, signals, context

[Exa](https://exa.ai/) is a semantic search API. Signalis uses it for three operations, each independently toggleable:

**Domain resolution** — records with company names but no domains: Exa locates the correct website. Runs first, since signals and context need a domain.

**Signal generation** — Exa searches for recent hiring, funding, and expansion activity. An AI model (OpenAI or Anthropic) extracts the strongest timing trigger per company.

**Context generation** — Exa fetches the company's own website. The AI distils it into a 1-2 sentence description of what they do and who they serve.

Each toggle is an independent yes/no — run all three, just one, or none.

Requires: `EXA_API_KEY` + one of `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

### Apify — dataset loading

[Apify](https://apify.com/) is a web scraping platform. Public datasets require no authentication. Private datasets need a token.

Requires: `APIFY_API_TOKEN` (private datasets only)

---

## ⚯  Connector

Once you have shaped your supply and demand CSVs, run the Connector to match them, enrich contacts, generate intro emails, and optionally send to a campaign platform.

```bash
signalis connect setup       # First-time API key configuration
signalis connect run supply.csv demand.csv
```

Or press **C** from the main menu for the guided flow.

### The Connector Pipeline

```
  supply.csv  +  demand.csv
      │
      ├─ 1. Normalize        Standardise both datasets to a shared schema
      ├─ 2. Match            Score every supply–demand pair (industry, signal, size, alignment)
      ├─ 3. Enrich           Find missing emails via Apollo → Anymail Finder cascade
      ├─ 4. AI Intros        Generate personalised intro emails per matched pair
      ├─ 5. Send             Push to Instantly.ai or Plusvibe campaign (optional)
      └─ 6. Export           Matched CSV with intros and enrichment written to output/
```

### Required keys for enrichment and intros

```env
# Contact enrichment
APOLLO_API_KEY=
ANYMAIL_API_KEY=

# AI intro generation — same key used by Shaper
OPENAI_API_KEY=    # or ANTHROPIC_API_KEY

# Campaign sending (optional)
INSTANTLY_API_KEY=
```

Run `signalis connect setup` to configure all Connector keys interactively — they are written to the same `.env` file as the Shaper keys.

---

## ▲  Configuration

```bash
signalis setup
```

Or press **S** from the main menu. Keys are written to `.env` and take effect immediately — no restart needed.

To set keys manually:

```bash
cp .env.example .env
```

```env
# Apify — only needed for private datasets
APIFY_API_TOKEN=

# Exa — domain resolution, signal generation, company context
EXA_API_KEY=

# AI provider for signal synthesis — pick one
AI_PROVIDER=openai
OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
```

Check which services are active:

```bash
signalis config
```

---

## ∴  Project Structure

```
  signalis-framework/
  ├── pyproject.toml          Package config and entry point
  ├── install.sh              One-command install — macOS / Linux
  ├── install.bat             One-command install — Windows
  ├── .env.example            API key template
  │
  ├── core/
  │   ├── config.py           Environment config and settings
  │   └── models.py           FieldMapping data model
  │
  ├── shaper/
  │   ├── cli.py              Interactive CLI and all commands
  │   ├── banner.py           UI helpers — progress, panels, tables
  │   ├── loaders/            CSV and Apify loading
  │   ├── mappers/            Auto-mapping and interactive mapping
  │   ├── normalizers/        Domain, name, email normalization
  │   ├── signals/            Signal processing, prefix, global
  │   ├── exporters/          Timestamped CSV export
  │   └── services/
  │       ├── exa_signal.py   Exa search + AI signal + context synthesis
  │       └── exa_domain.py   Domain resolution via Exa
  │
  └── connector/
      ├── cli.py              Connector CLI — run, setup, cache commands
      ├── matcher.py          Scoring engine — industry, signal, alignment
      ├── enrichment.py       Apollo → Anymail Finder → ConnectorAgent cascade
      ├── intro_generator.py  AI intro template filling (OpenAI / Anthropic)
      ├── senders.py          Instantly.ai and Plusvibe sending
      ├── models.py           NormalizedRecord, Match, EnrichmentResult
      ├── config.py           ConnectorConfig — env vars for all connector services
      ├── semantic_expansion.py  Keyword expansion for matching
      ├── enrichment_cache.py    90-day TTL enrichment cache (~/.connector-cli/)
      ├── csv_normalizer.py   CSV loading and schema normalisation
      └── interactive.py      Setup wizard
```

---

## ⊕  Roadmap

The foundation is complete. More data sources, scoring refinements, and campaign integrations coming soon.

---

## ⊗  Troubleshooting

**Python not found**
Install Python 3.9 or later and ensure it is on your PATH.
- macOS: `brew install python3`
- Linux: `sudo apt install python3 python3-venv`
- Windows: [python.org](https://www.python.org/downloads/) — check **Add Python to PATH**

**No module named 'click'** or similar import errors
If you bypassed the installer, activate the virtual environment manually:
```bash
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate.bat       # Windows CMD
```
Then run `pip install -e .[ai]`.

**Permission denied on install.sh**
```bash
chmod +x install.sh && ./install.sh
```

**CSV shows garbled text**
Save the file as UTF-8 from your spreadsheet application before importing.

**Apify dataset not loading**
Confirm the dataset ID is correct. For private datasets, verify `APIFY_API_TOKEN` is set — run `signalis config` to check.

**Exa enrichment returns no signals**
Ensure both `EXA_API_KEY` and an AI provider key (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`) are set. Domain resolution runs before signal generation — records without a domain or company name are skipped.

---

## ─  License

MIT
