"""
Connector banner — uses shared console from shaper, keeps connector-specific displays.
"""

from rich.panel import Panel

# Use shared console so output is consistent with main shaper UI
from shaper.banner import console

TAGLINE = "Match Supply to Demand • Enrich Data • Generate AI Intros • Send Campaigns"
VERSION = "v1.0.0"


def show_banner():
    """Display connector header (no ASCII art — only main Signalis has that)."""
    console.print()
    console.print("[bold cyan]⚯ Connector[/bold cyan]")
    console.print(f"[dim]{TAGLINE}[/dim]")
    console.print()


def show_welcome():
    """Show welcome message."""
    welcome = Panel(
        "[bold cyan]Welcome to Connector CLI![/bold cyan]\n\n"
        "This tool helps you:\n"
        "  [green]☉[/green] Match demand companies with supply providers\n"
        "  [green]☉[/green] Find missing emails automatically\n"
        "  [green]☉[/green] Generate AI-powered intro emails\n\n"
        "[dim]Let's get started...[/dim]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(welcome)
    console.print()


def show_step(step_num: int, title: str, description: str = ""):
    """Show a step header."""
    step_text = f"[bold cyan]Step {step_num}:[/bold cyan] [bold white]{title}[/bold white]"
    if description:
        step_text += f"\n[dim]{description}[/dim]"
    console.print(step_text)
    console.print()


def show_success(message: str):
    """Show success message."""
    console.print(f"[green]☉[/green] {message}")


def show_error(message: str):
    """Show error message."""
    console.print(f"[red]☿[/red] {message}", style="red")


def show_warning(message: str):
    """Show warning message."""
    console.print(f"[yellow]▲[/yellow] {message}", style="yellow")


def show_info(message: str):
    """Show info message."""
    console.print(f"[blue]◈[/blue] {message}", style="blue")


def show_results_summary(stats: dict):
    """Show results summary in a panel."""
    total_matches = stats.get('total_matches', 0)
    unique_demands = stats.get('unique_demands_matched', 0)
    avg_per_demand = total_matches / unique_demands if unique_demands > 0 else 0

    summary = Panel(
        f"[bold green]☉ Flow Complete![/bold green]\n\n"
        f"[white]Total Demand:[/white] {stats.get('total_demand', 0)}\n"
        f"[white]Total Supply:[/white] {stats.get('total_supply', 0)}\n"
        f"[white]Total Matches:[/white] {total_matches}\n"
        f"[white]Demands Matched:[/white] {unique_demands}\n"
        f"[white]Avg per Demand:[/white] {avg_per_demand:.1f}\n"
        f"[white]Average Score:[/white] {stats.get('avg_score', 0)}/100\n\n"
        f"[dim]Check your output directory for results![/dim]",
        title="[bold]Results Summary[/bold]",
        border_style="green",
        padding=(1, 2)
    )
    console.print()
    console.print(summary)
