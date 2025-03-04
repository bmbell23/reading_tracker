"""
CLI Display Utilities
===================

Shared utilities for CLI display formatting and output generation.
Provides consistent formatting across all CLI tools.
"""

from typing import Any, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def format_date(date_value: Optional[datetime]) -> str:
    """Format date value or return 'Not set' if None"""
    return date_value.strftime("%Y-%m-%d") if date_value else "Not set"

def create_details_panel(content: str, title: str = "Details") -> Panel:
    """Create a formatted panel with content and title"""
    return Panel(content, title=f"[bold cyan]{title}[/bold cyan]")

def create_book_panel(title: str, author_first: str, author_second: Optional[str] = None) -> Panel:
    """Create a formatted panel with book information"""
    author = f"{author_first} {author_second or ''}"
    content = f"[bold]{title}[/bold]\nby {author}"
    return create_details_panel(content, "Book Details")

def create_info_table(rows: list[tuple[str, Any]], show_header: bool = False) -> Table:
    """Create a formatted table for displaying information"""
    table = Table(show_header=show_header, box=None)
    for label, value in rows:
        table.add_row(f"{label}:", str(value))
    return table

def display_reading_details(reading_details: dict) -> None:
    """Display formatted reading details"""
    if not reading_details:
        console.print("[red]Reading not found[/red]")
        return

    # Book Information
    console.print(create_book_panel(
        reading_details['book']['title'],
        reading_details['book']['author_first'],
        reading_details['book']['author_second']
    ))

    # Reading Session Details
    details_rows = [
        ("Reading ID", str(reading_details['reading_id'])),
        ("Format", reading_details['media']),
        ("Started", format_date(reading_details['dates']['started'])),
        ("Finished", format_date(reading_details['dates']['finished'])),
        ("Est. Start", format_date(reading_details['dates']['estimated_start'])),
        ("Est. End", format_date(reading_details['dates']['estimated_end']))
    ]
    console.print(create_details_panel(
        create_info_table(details_rows),
        "Reading Details"
    ))

    # Progress Information
    if any(reading_details['progress'].values()):
        progress_rows = [
            ("Days Elapsed", str(reading_details['progress']['days_elapsed'] or 0)),
            ("Days Estimate", str(reading_details['progress']['days_estimate'] or 0)),
            ("Days Delta", str(reading_details['progress']['days_delta'] or 0))
        ]
        console.print(create_details_panel(
            create_info_table(progress_rows),
            "Progress"
        ))

    # Chain Information
    chain_rows = [
        ("Previous Reading", str(reading_details['chain']['previous_id'] or "None"))
    ]
    if reading_details['chain']['next_id']:
        chain_rows.append((
            "Next Reading",
            f"{reading_details['chain']['next_id']} ({reading_details['chain']['next_title']})"
        ))
    else:
        chain_rows.append(("Next Reading", "None"))
    
    console.print(create_details_panel(
        create_info_table(chain_rows),
        "Chain Information"
    ))
