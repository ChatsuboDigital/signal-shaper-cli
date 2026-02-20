"""
Interactive field mapper

Provides an interactive UI for manually mapping source fields to target fields.
"""

from typing import List, Optional, Dict, Any
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from core.models import FieldMapping
from ..banner import console


# Friendly display names for the 4 mapper-owned fields
FRIENDLY = {
    'domain':       'Domain',
    'company_name': 'Company Name',
    'full_name':    'Full Name',
    'email':        'Email',
}

# Fields handled exclusively in Step 5 — never shown in the mapper
STEP5_FIELDS = {'signal', 'company_description'}


class InteractiveMapper:
    """
    Interactive field mapping with Rich UI.

    Example:
        mapper = InteractiveMapper(source_headers, sample_records)
        mapping = mapper.map()
    """

    def __init__(self, source_headers: List[str], sample_records: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize interactive mapper.

        Args:
            source_headers: List of source column names
            sample_records: Optional list of sample records for preview (recommended 3-5 records)
        """
        self.source_headers = source_headers
        self.sample_records = sample_records or []

    def map(self, auto_mapping: Optional[FieldMapping] = None) -> FieldMapping:
        """
        Interactively map fields.

        Args:
            auto_mapping: Optional pre-detected mapping to use as defaults

        Returns:
            FieldMapping with user-selected mappings
        """
        console.print()
        console.rule("[bold cyan]Field Mapping[/bold cyan]", style="cyan")
        console.print("[dim]Match your source columns to the standard export format.[/dim]")
        console.print("[dim]Type a column [bold]#[/bold] or [bold]name[/bold] at each prompt · Enter = accept auto / skip[/dim]")

        # Show available source columns once, near the top
        console.print()
        self._show_source_columns()

        # If auto-mapping provided and complete, offer to accept it outright
        if auto_mapping and auto_mapping.is_complete():
            console.print()
            console.print("[green]☉ All required fields auto-detected[/green]")
            self._show_auto_mapping(auto_mapping)

            if Confirm.ask("\n[cyan]Use auto-detected mapping?[/cyan]", default=True):
                console.print("[green]☉ Auto-mapping accepted[/green]")
                return auto_mapping

            console.print("\n[yellow]Manual mapping mode[/yellow]")

        mapping = FieldMapping()

        # ── Group 1: Identifier ──────────────────────────────────────────────
        console.print()
        console.rule(
            "[bold cyan]Identifier[/bold cyan]  [dim]need at least one[/dim]",
            style="cyan"
        )
        console.print("[dim]At least one is required — Exa resolves domain from company name if missing[/dim]\n")

        mapping.domain = self._map_field(
            "Domain", "company website · e.g. acme.com",
            auto_mapping.domain if auto_mapping else None,
            step="1/2"
        )
        mapping.company_name = self._map_field(
            "Company Name", "company or organisation · e.g. Acme Corp",
            auto_mapping.company_name if auto_mapping else None,
            step="2/2"
        )

        # ── Group 2: Contact ─────────────────────────────────────────────────
        console.print()
        console.rule(
            "[bold yellow]Contact[/bold yellow]  [dim]optional[/dim]",
            style="yellow"
        )
        console.print("[dim]Press Enter to skip[/dim]\n")

        mapping.full_name = self._map_field(
            "Full Name", "contact's full name · e.g. Jane Smith",
            auto_mapping.full_name if auto_mapping else None,
            step="1/2"
        )
        mapping.email = self._map_field(
            "Email", "contact email · e.g. jane@acme.com",
            auto_mapping.email if auto_mapping else None,
            step="2/2"
        )

        # Final summary
        console.print()
        console.rule("[bold green]Mapping Complete[/bold green]", style="green")
        self._show_mapping_summary(mapping)

        return mapping

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _show_source_columns(self):
        """Display available source columns with sample data."""
        if self.sample_records:
            table = Table(title="Source Columns", show_header=True)
            table.add_column("#", style="dim", width=4)
            table.add_column("Column Name", style="cyan bold", width=25)
            table.add_column("Sample Values", style="white", overflow="fold")

            for i, header in enumerate(self.source_headers, 1):
                samples = []
                for record in self.sample_records[:3]:
                    val = record.get(header, "")
                    if val:
                        if isinstance(val, dict):
                            val = val.get('name') or val.get('title') or val.get('url') or str(val)
                        val_str = str(val)[:40]
                        if len(str(val)) > 40:
                            val_str += "..."
                        samples.append(val_str)

                sample_text = " | ".join(samples) if samples else "[dim]<empty>[/dim]"
                table.add_row(f"{i}.", header, sample_text)
        else:
            table = Table(title="Source Columns", show_header=False)
            table.add_column("Index", style="dim", width=6)
            table.add_column("Column Name", style="cyan")
            for i, header in enumerate(self.source_headers, 1):
                table.add_row(f"{i}.", header)

        console.print(table)

    def _show_auto_mapping(self, mapping: FieldMapping):
        """Display auto-detected mapping (mapper fields only, friendly names)."""
        table = Table(title="Auto-Detected Mapping", show_header=True, border_style="cyan")
        table.add_column("Field", style="cyan", width=16)
        table.add_column("Source Column", style="green")

        for field, label in FRIENDLY.items():
            source = getattr(mapping, field, None)
            if source is not None:
                table.add_row(label, source)

        console.print(table)
        console.print("[dim]Signal & Context → configured in next step[/dim]")

    def _show_mapping_summary(self, mapping: FieldMapping):
        """Display final mapping summary (4 fields, logical order)."""
        table = Table(
            title="[bold cyan]Mapping Summary[/bold cyan]",
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
            pad_edge=False,
            expand=False
        )
        table.add_column("Field", style="cyan bold", width=16)
        table.add_column("Source Column", style="white", width=25)
        table.add_column("Status", justify="center", width=10)

        required_fields = {'domain', 'company_name'}
        mapped_required = 0

        for field, label in FRIENDLY.items():
            source = getattr(mapping, field, None)
            is_req = field in required_fields

            if source is not None:
                status = "[green]☉[/green]"
                if is_req:
                    mapped_required += 1
            elif is_req:
                status = "[red]☿[/red]"
            else:
                status = "[dim]—[/dim]"

            display = f"◆ {label}" if is_req else f"  {label}"
            table.add_row(display, source or "[dim]-[/dim]", status)

        console.print(table)
        console.print()

        if mapped_required == 2:
            console.print("[bold green]☉ Both identifiers mapped[/bold green]")
        elif mapped_required == 1:
            console.print("[yellow]▲ One identifier mapped — Exa can fill the other[/yellow]")
        else:
            console.print("[red]☿ No identifier mapped — need domain or company name to proceed[/red]")

        total_mapped = sum(1 for f in FRIENDLY if getattr(mapping, f, None))
        console.print(f"[dim]{total_mapped} of 4 fields mapped · Signal & Context → Step 5[/dim]")

    def _inline_preview(self, column_name: str) -> str:
        """
        Return a one-line preview string for the selected column.

        Returns e.g. "acme.com · bolt.io · stripe.dev  (100%)" or ""
        """
        if not self.sample_records:
            return ""

        values = []
        total = min(5, len(self.sample_records))
        for record in self.sample_records[:total]:
            val = record.get(column_name, "")
            if val:
                if isinstance(val, dict):
                    val = val.get('name') or val.get('title') or val.get('url') or str(val)
                val_str = str(val)[:35]
                if len(str(val)) > 35:
                    val_str += "…"
                values.append(val_str)

        if not values:
            return ""

        fill_rate = len(values) / total * 100
        samples = " · ".join(values[:3])
        rate_tag = f"({fill_rate:.0f}%)"

        if fill_rate < 50:
            return f"▲ {samples}  [dim]{rate_tag} sparse[/dim]"
        return f"{samples}  [dim]{rate_tag}[/dim]"

    def _map_field(
        self,
        field_name: str,
        hint: str,
        default: Optional[str] = None,
        step: str = ""
    ) -> Optional[str]:
        """
        Map a single field interactively.

        Args:
            field_name: Display name of target field
            hint: Short description + example shown inline
            default: Default source column (from auto-mapping)
            step: Progress indicator (e.g., "1/2")

        Returns:
            Selected source column name or None
        """
        # Compact header: "Domain (1/2)  company website · e.g. acme.com"
        step_tag = f" [dim]({step})[/dim]" if step else ""
        console.print(f"[bold cyan]{field_name}[/bold cyan]{step_tag}  [dim]{hint}[/dim]")

        if default:
            console.print(f"  [green]☉ auto:[/green] [white]{default}[/white]")

        while True:
            user_input = Prompt.ask(
                "  [cyan]→[/cyan]",
                default=default or "",
                show_default=False
            )

            # Skip if empty
            if not user_input:
                console.print("  [dim]— skipped[/dim]")
                return None

            # Use the default value directly (user pressed Enter with a default)
            if user_input == default and default in self.source_headers:
                preview = self._inline_preview(default)
                console.print(f"  [green]☉ {default}[/green]  [dim]{preview}[/dim]" if preview else f"  [green]☉ {default}[/green]")
                return default

            # Numeric index
            if user_input.isdigit():
                index = int(user_input) - 1
                if 0 <= index < len(self.source_headers):
                    selected = self.source_headers[index]
                    preview = self._inline_preview(selected)
                    console.print(f"  [green]☉ {selected}[/green]  [dim]{preview}[/dim]" if preview else f"  [green]☉ {selected}[/green]")
                    return selected
                else:
                    console.print(f"  [red]☿ Invalid — must be 1–{len(self.source_headers)}[/red]")
                    continue

            # Exact name match
            if user_input in self.source_headers:
                preview = self._inline_preview(user_input)
                console.print(f"  [green]☉ {user_input}[/green]  [dim]{preview}[/dim]" if preview else f"  [green]☉ {user_input}[/green]")
                return user_input

            # Fuzzy / substring match
            matches = [h for h in self.source_headers if user_input.lower() in h.lower()]
            if len(matches) == 1:
                preview = self._inline_preview(matches[0])
                console.print(f"  [green]☉ {matches[0]}[/green]  [dim]{preview}[/dim]" if preview else f"  [green]☉ {matches[0]}[/green]")
                return matches[0]
            elif matches:
                console.print(f"  [yellow]Did you mean:[/yellow] {', '.join(matches[:5])}")
            else:
                short = ', '.join(self.source_headers[:5])
                more = f' (+{len(self.source_headers)-5} more)' if len(self.source_headers) > 5 else ''
                console.print(f"  [red]☿ Not found:[/red] '{user_input}'")
                console.print(f"  [dim]Columns: {short}{more}[/dim]")
