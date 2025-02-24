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

    def print_reading(self, reading):
        """
        Print a specific reading instance in a formatted way

        Args:
            reading: The Reading instance to print
        """
        self.console.print(f"\n[bold]{reading.book.title}[/bold]")
        self.console.print(f"Reading ID: {reading.id}")
        self.console.print(f"Book ID: {reading.book.id}")

        # Format dates
        start_date = reading.date_started or reading.date_est_start
        end_date = reading.date_finished_actual or reading.date_est_end

        if start_date:
            self.console.print(f"Start: {start_date}")
        if end_date:
            self.console.print(f"End: {end_date}")

        # Show media type with appropriate color
        media_color = self._get_media_color(reading.media)
        self.console.print(f"Media: [{media_color}]{reading.media}[/{media_color}]")

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
            self.print_reading(reading)


if __name__ == "__main__":
    # Example usage
    queries = CommonQueries()

    # Example: Search for a specific book
    title_to_search = input("Enter book title to search for: ")
    exact = input("Exact match? (y/n): ").lower() == 'y'

    queries.print_readings_by_title(title_to_search, exact)
