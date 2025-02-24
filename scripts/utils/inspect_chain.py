import sys
from pathlib import Path
from scripts.utils.paths import find_project_root
from datetime import datetime, date

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(project_root))

from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book
from sqlalchemy import inspect
from scripts.queries.common_queries import CommonQueries
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule

console = Console()

def create_section_header(title, style="bold cyan"):
    """Create a visually distinct section header"""
    console.print(Rule(style=style))
    console.print(f"[{style}]{title}[/{style}]", justify="center")
    console.print(Rule(style=style))

def inspect_chain_around_book(title_fragment):
    """Display the reading chain around a book, focusing on upcoming books in 2025"""
    queries = CommonQueries()
    session = SessionLocal()
    target_year = 2025  # Specifically looking at 2025 books

    try:
        # Find the target book's reading
        target = (session.query(Reading)
                 .join(Book)
                 .filter(Book.title.ilike(f"%{title_fragment}%"))
                 .first())

        if not target:
            console.print(Panel(
                f"[red]No reading found with title containing '{title_fragment}'[/red]",
                border_style="red"
            ))
            return

        # Print header
        console.print("\n")
        console.print(Panel(
            f"[bold white]Reading Chain Analysis (2025)[/bold white]\n"
            f"[dim]Showing reading chain around:[/dim] [cyan]{target.book.title}[/cyan]",
            border_style="cyan",
            expand=False
        ))

        # Get just 1-2 most recent completed books
        before_chain = (session.query(Reading)
                       .join(Book)
                       .filter(Reading.date_finished_actual.isnot(None))
                       .filter(Reading.id_previous == target.id_previous)
                       .order_by(Reading.date_finished_actual.desc())
                       .limit(2)
                       .all())

        # Get upcoming books for 2025
        after_chain = (session.query(Reading)
                      .join(Book)
                      .filter(Reading.date_est_start >= date(2025, 1, 1))
                      .filter(Reading.date_est_start < date(2026, 1, 1))
                      .filter(Reading.date_finished_actual.is_(None))
                      .order_by(Reading.date_est_start)
                      .all())

        # Print recent completed books
        if before_chain:
            console.print("\n")
            create_section_header("📚 RECENT COMPLETED", "blue")
            with console.capture() as capture:
                for reading in before_chain:
                    queries.print_readings_by_title(reading.book.title, exact_match=True)
            console.print(Panel(capture.get(), border_style="blue", expand=False))

        # Print target book
        console.print("\n")
        create_section_header("🎯 CURRENT BOOK", "yellow")
        with console.capture() as capture:
            queries.print_readings_by_title(target.book.title, exact_match=True)
        console.print(Panel(capture.get(), border_style="yellow", expand=False))

        # Print upcoming books
        if after_chain:
            console.print("\n")
            create_section_header("📚 UPCOMING BOOKS (2025)", "green")
            with console.capture() as capture:
                for reading in after_chain:
                    queries.print_readings_by_title(reading.book.title, exact_match=True)
            console.print(Panel(capture.get(), border_style="green", expand=False))

        # Print summary
        total_books = len(before_chain) + 1 + len(after_chain)
        console.print("\n")
        console.print(Panel(
            f"[bold white]Chain Summary[/bold white]\n"
            f"Recent Completed: [blue]{len(before_chain)}[/blue]\n"
            f"Upcoming Books (2025): [green]{len(after_chain)}[/green]\n"
            f"Total in Chain: [yellow]{total_books}[/yellow]",
            border_style="cyan",
            expand=False
        ))

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print(Panel(
            "[red]Usage: python inspect_chain.py <book_title_fragment>[/red]",
            border_style="red"
        ))
        sys.exit(1)
    inspect_chain_around_book(sys.argv[1])
