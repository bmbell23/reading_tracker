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
    """Display the reading chain around a book"""
    queries = CommonQueries()
    session = SessionLocal()

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
            f"[bold white]Reading Chain Analysis[/bold white]\n"
            f"[dim]Showing reading chain around:[/dim] [cyan]{target.book.title}[/cyan]",
            border_style="cyan",
            expand=False
        ))

        # Get previous books by following id_previous chain
        before_chain = []
        current = session.get(Reading, target.id_previous)
        while current and len(before_chain) < 20:  # Show up to 20 previous books
            before_chain.append(current)
            current = session.get(Reading, current.id_previous)

        # Get next books by following the chain forward
        after_chain = []
        current = target
        while current and len(after_chain) < 20:  # Show up to 20 next books
            next_reading = session.query(Reading).filter(Reading.id_previous == current.id).first()
            if not next_reading:
                break
            after_chain.append(next_reading)
            current = next_reading

        # Print previous books
        if before_chain:
            create_section_header("📚 PREVIOUS BOOKS", "blue")
            with console.capture() as capture:
                for reading in reversed(before_chain):  # Show in chronological order
                    queries.print_reading(reading)
            console.print(Panel(capture.get().strip(), border_style="blue", expand=False))

        # Print target book
        create_section_header("🎯 TARGET BOOK", "yellow")
        with console.capture() as capture:
            queries.print_reading(target)
        console.print(Panel(capture.get().strip(), border_style="yellow", expand=False))

        # Print next books
        if after_chain:
            create_section_header("📚 NEXT BOOKS", "green")
            with console.capture() as capture:
                for reading in after_chain:
                    queries.print_reading(reading)
            console.print(Panel(capture.get().strip(), border_style="green", expand=False))

        # Print summary
        total_books = len(before_chain) + 1 + len(after_chain)
        console.print(Panel(
            f"[bold white]Chain Summary[/bold white]\n"
            f"Previous Books: [blue]{len(before_chain)}[/blue]\n"
            f"Next Books: [green]{len(after_chain)}[/green]\n"
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
