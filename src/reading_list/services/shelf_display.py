"""Service for displaying books organized by physical shelves."""
from typing import List, Dict
from sqlalchemy import text, update
from ..models.base import SessionLocal
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

class ShelfDisplayService:
    def __init__(self):
        self.console = Console()

    def get_physical_books(self) -> List[Dict]:
        """Get all physically owned books with their shelf information."""
        with SessionLocal() as session:
            query = text("""
                SELECT
                    b.id as book_id,
                    b.title,
                    b.author_name_first,
                    b.author_name_second,
                    b.date_published,
                    i.id as inv_id,
                    i.location as shelf_location
                FROM books b
                JOIN inv i ON b.id = i.book_id
                WHERE i.owned_physical = TRUE
                ORDER BY
                    COALESCE(i.location, 'Unshelved') ASC,
                    COALESCE(b.author_name_first, b.author_name_second) ASC,
                    b.author_name_second ASC,
                    b.date_published ASC,
                    b.title ASC
            """)
            results = session.execute(query).mappings().all()
            return [dict(r) for r in results]

    def update_book_location(self, inv_id: int, location: str) -> None:
        """Update the location for a book in the inventory."""
        with SessionLocal() as session:
            query = text("""
                UPDATE inv
                SET location = :location
                WHERE id = :inv_id
            """)
            session.execute(query, {"location": location, "inv_id": inv_id})
            session.commit()

    def get_existing_shelves(self) -> List[str]:
        """Get list of existing shelf locations."""
        with SessionLocal() as session:
            query = text("""
                SELECT DISTINCT location
                FROM inv
                WHERE location IS NOT NULL
                ORDER BY location
            """)
            results = session.execute(query)
            return [r[0] for r in results if r[0]]

    def format_date(self, date_value) -> str:
        """Format date value or return empty string if None"""
        if not date_value:
            return ""
        if isinstance(date_value, str):
            return date_value[:4]  # Just take the year part of the string
        try:
            return date_value.strftime("%Y")
        except AttributeError:
            return str(date_value)

    def prompt_for_shelving(self, unshelved_books: List[Dict]) -> None:
        """Prompt user to provide locations for unshelved books."""
        if not unshelved_books:
            return

        self.console.print("\n[bold yellow]Found unshelved books:[/bold yellow]")

        # Get existing shelves for suggestions
        existing_shelves = self.get_existing_shelves()

        for book in unshelved_books:
            self.console.print(f"\n[cyan]Book:[/cyan] {book['title']}")
            if book['author_name_first'] or book['author_name_second']:
                author = " ".join(filter(None, [book['author_name_first'], book['author_name_second']]))
                self.console.print(f"[cyan]Author:[/cyan] {author}")
            if book['date_published']:
                self.console.print(f"[cyan]Published:[/cyan] {self.format_date(book['date_published'])}")

            if existing_shelves:
                self.console.print("\n[dim]Existing shelves:[/dim]")
                for shelf in existing_shelves:
                    self.console.print(f"[dim]- {shelf}[/dim]")

            if Confirm.ask("Would you like to shelve this book?", default=True):
                location = Prompt.ask("Enter shelf location")
                if location.strip():
                    self.update_book_location(book['inv_id'], location.strip())
                    self.console.print(f"[green]Updated location to: {location}[/green]")

                    # Add new location to existing shelves if it's not there
                    if location not in existing_shelves:
                        existing_shelves.append(location)
                        existing_shelves.sort()

    def display_books(self, show_count_only: bool = False, prompt_unshelved: bool = False) -> None:
        """Display physically owned books in a formatted table."""
        books = self.get_physical_books()

        # Group books by shelf
        shelved_books: Dict[str, List[Dict]] = {}
        for book in books:
            shelf = book['shelf_location'] or 'Unshelved'
            if shelf not in shelved_books:
                shelved_books[shelf] = []
            shelved_books[shelf].append(book)

        if prompt_unshelved and 'Unshelved' in shelved_books:
            self.prompt_for_shelving(shelved_books['Unshelved'])
            # Refresh the book list after updates
            return self.display_books(show_count_only=show_count_only, prompt_unshelved=False)

        if show_count_only:
            # Display only shelf counts
            table = Table(
                title="[bold cyan]Books per Shelf[/bold cyan]",
                show_header=True,
                header_style="bold magenta"
            )

            table.add_column("Shelf", style="white")
            table.add_column("Book Count", justify="right", style="green")

            total_books = 0
            for shelf, shelf_books in shelved_books.items():
                count = len(shelf_books)
                total_books += count
                table.add_row(shelf, str(count))

            table.add_row("[bold]Total[/bold]", f"[bold]{total_books}[/bold]")
            self.console.print(table)
            return

        # Display detailed shelf contents
        for shelf, shelf_books in shelved_books.items():
            table = Table(
                title=f"[bold cyan]Shelf: {shelf} ({len(shelf_books)} books)[/bold cyan]",
                show_header=True,
                header_style="bold magenta"
            )

            table.add_column("Title", style="white")
            table.add_column("Author", style="white")
            table.add_column("Published", style="white", justify="right")

            for book in shelf_books:
                author_parts = [
                    book['author_name_first'],
                    book['author_name_second']
                ]
                author = " ".join(filter(None, author_parts)) or "Unknown Author"

                table.add_row(
                    book['title'],
                    author,
                    self.format_date(book['date_published'])
                )

            self.console.print(table)
            self.console.print()  # Add spacing between shelves