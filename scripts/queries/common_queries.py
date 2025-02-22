from sqlalchemy import select
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import date
from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book

class CommonQueries:
    """Common database queries that are frequently used across the application"""

    def __init__(self):
        self.session = SessionLocal()
        self.console = Console()

    def __del__(self):
        """Ensure the session is closed when the object is destroyed"""
        self.session.close()

    def get_readings_by_title(self, title: str, exact_match: bool = True) -> list:
        """
        Get all readings for a book with the specified title

        Args:
            title: The title to search for
            exact_match: If True, matches title exactly. If False, uses LIKE with wildcards

        Returns:
            List of Reading objects with associated Book data
        """
        try:
            query = (
                select(Reading)
                .join(Book, Reading.book_id == Book.id)
            )

            if exact_match:
                query = query.where(Book.title == title)
            else:
                query = query.where(Book.title.ilike(f"%{title}%"))

            results = self.session.execute(query).scalars().all()

            if not results:
                self.console.print(f"\n[yellow]No readings found for book title: '{title}'[/yellow]")
                return []

            return results

        except Exception as e:
            self.console.print(f"\n[red]Error executing query: {e}[/red]")
            return []

    def _get_media_color(self, media: str) -> str:
        """Get color based on media type"""
        media_lower = media.lower()
        if media_lower == 'audio':
            return 'orange1'
        elif media_lower == 'hardcover':
            return 'purple'
        elif media_lower == 'kindle':
            return 'blue'
        return 'white'

    def print_readings_by_title(self, title: str, exact_match: bool = True):
        """
        Print all readings for a book in a formatted way

        Args:
            title: The title to search for
            exact_match: If True, matches title exactly. If False, uses LIKE with wildcards
        """
        readings = self.get_readings_by_title(title, exact_match)

        if not readings:
            return

        self.console.print(f"\n[bold cyan]Readings for '{title}':[/bold cyan]")

        for reading in readings:
            # Get subsequent reading if it exists
            next_reading = (self.session.query(Reading)
                          .filter(Reading.id_previous == reading.id)
                          .first())

            # Get previous reading if it exists
            prev_reading = (self.session.get(Reading, reading.id_previous)
                          if reading.id_previous else None)

            # Create table for reading details
            table = Table(show_header=False, box=None)
            table.add_column("Field", style="dim")
            table.add_column("Value")

            # Get media color
            media_color = self._get_media_color(reading.media)

            # Add rows to table
            table.add_row("Reading ID", f"[yellow]{reading.id}[/yellow]")
            table.add_row("Book ID", f"[yellow]{reading.book_id}[/yellow]")
            table.add_row("Book", f"[bold white]{reading.book.title}[/bold white]")
            table.add_row("Word Count", f"[cyan]{reading.book.word_count:,}[/cyan]" if reading.book.word_count else "[dim]None[/dim]")
            table.add_row("Media", f"[{media_color}]{reading.media}[/{media_color}]")

            # Previous reading info
            prev_book = f"[italic]{prev_reading.book.title}[/italic]" if prev_reading else "[dim]None[/dim]"
            table.add_row(
                "Previous Reading",
                f"ID: [yellow]{reading.id_previous or 'None'}[/yellow], Book: {prev_book}"
            )

            # Next reading info
            next_book = f"[italic]{next_reading.book.title}[/italic]" if next_reading else "[dim]None[/dim]"
            table.add_row(
                "Next Reading",
                f"ID: [yellow]{next_reading.id if next_reading else 'None'}[/yellow], Book: {next_book}"
            )

            # Est. Days to Read
            table.add_row(
                "Est. Days to Read",
                f"[cyan]{reading.days_estimate}[/cyan]" if reading.days_estimate else "[dim]None[/dim]"
            )

            # Dates
            table.add_row(
                "Started",
                f"[green]{reading.date_started}[/green]" if reading.date_started else "[dim]None[/dim]"
            )
            table.add_row(
                "Finished",
                f"[green]{reading.date_finished_actual}[/green]" if reading.date_finished_actual else "[dim]None[/dim]"
            )
            table.add_row(
                "Est. Start",
                f"[blue]{reading.date_est_start}[/blue]" if reading.date_est_start else "[dim]None[/dim]"
            )
            table.add_row(
                "Est. End",
                f"[blue]{reading.date_est_end}[/blue]" if reading.date_est_end else "[dim]None[/dim]"
            )

            if reading.rating_enjoyment:
                table.add_row("Enjoyment Rating", f"[yellow]{reading.rating_enjoyment}★[/yellow]")

            # Create panel with table
            panel = Panel(
                table,
                border_style="bright_black",
                padding=(1, 2),
                title=f"[{media_color}]Reading Details[/{media_color}]",
            )

            self.console.print(panel)
            self.console.print()


if __name__ == "__main__":
    # Example usage
    queries = CommonQueries()

    # Example: Search for a specific book
    title_to_search = input("Enter book title to search for: ")
    exact = input("Exact match? (y/n): ").lower() == 'y'

    queries.print_readings_by_title(title_to_search, exact)
