"""
Banner and UI components for Signalis Framework
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Global console instance
console = Console()


VERSION = "1.0.0"
TAGLINE = "Transform raw data into outreach-ready CSVs"


def show_banner():
    """Display ASCII art banner"""
    art = (
        "[bold cyan]"
        "███████╗██╗ ██████╗ ███╗   ██╗  █████╗ ██╗     ██╗███████╗\n"
        "██╔════╝██║██╔════╝ ████╗  ██║ ██╔══██╗██║     ██║██╔════╝\n"
        "███████╗██║██║  ███╗██╔██╗ ██║ ███████║██║     ██║███████╗\n"
        "╚════██║██║██║   ██║██║╚██╗██║ ██╔══██║██║     ██║╚════██║\n"
        "███████║██║╚██████╔╝██║ ╚████║ ██║  ██║███████╗██║███████║\n"
        "╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═╝  ╚═╝╚══════╝╚═╝╚══════╝"
        "[/bold cyan]"
    )
    panel = Panel(
        f"{art}\n\n[dim]{TAGLINE}[/dim]\n[dim]v{VERSION}[/dim]",
        border_style="cyan",
        padding=(1, 3),
    )
    console.print(panel)


def show_step(step: int, title: str, description: str = ""):
    """Show a step header"""
    console.print()
    header = f"[bold cyan]Step {step}: {title}[/bold cyan]"
    if description:
        console.print(f"{header}\n[dim]{description}[/dim]")
    else:
        console.print(header)


def show_success(message: str):
    """Show success message"""
    console.print(f"☉ [green]{message}[/green]")


def show_error(message: str):
    """Show error message"""
    console.print(f"☿ [red]{message}[/red]")


def show_warning(message: str):
    """Show warning message"""
    console.print(f"▲ [yellow]{message}[/yellow]")


def show_info(message: str):
    """Show info message"""
    console.print(f"◈ [blue]{message}[/blue]")


def show_preview_table(records: list, headers: list, limit: int = 5):
    """Display preview of data in a table"""
    table = Table(show_header=True, header_style="bold cyan")

    # Add columns
    for header in headers:
        table.add_column(header[:20], overflow="fold")  # Truncate long headers

    # Add rows (limit to preview count)
    for record in records[:limit]:
        row = [str(record.get(h, ""))[:30] for h in headers]  # Truncate long values
        table.add_row(*row)

    console.print(table)


def show_validation_summary(valid: int, warnings: int, total: int, avg_score: float):
    """Show validation summary"""
    panel = Panel(
        f"[bold]Validation Summary[/bold]\n\n"
        f"Total rows: [white]{total}[/white]\n"
        f"☉ Valid: [green]{valid}[/green] ({valid/total*100:.0f}%)\n"
        f"▲ Warnings: [yellow]{warnings}[/yellow]\n"
        f"Average quality score: [cyan]{avg_score:.0f}/100[/cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)


def show_signal_distribution(distribution: dict):
    """Show signal type distribution"""
    console.print("\n[bold cyan]Signal Type Distribution:[/bold cyan]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Signal Type", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Percentage", justify="right")

    total = sum(distribution.values())
    for signal_type, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        percentage = f"{count/total*100:.1f}%" if total > 0 else "0%"
        table.add_row(signal_type, str(count), percentage)

    console.print(table)


def show_export_summary(records_exported: int, output_path: str, duplicates_removed: int = 0):
    """Show export summary"""
    panel = Panel(
        f"[bold green]Export Complete![/bold green]\n\n"
        f"Records exported: [white]{records_exported}[/white]\n"
        f"Duplicates removed: [white]{duplicates_removed}[/white]\n"
        f"Output: [cyan]{output_path}[/cyan]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)


def create_progress() -> Progress:
    """Create a Rich progress bar"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )
