from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.reading import Reading
from ..models.book import Book
from ..models.base import SessionLocal
from rich.console import Console
from typing import Optional
from sqlalchemy import func

console = Console()

class CommonQueries:
    """Common database queries that are frequently used across the application"""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize common queries
        
        Args:
            session: SQLAlchemy session. If None, creates new session
        """
        self.session = session or SessionLocal()
        self.console = Console()

    def __del__(self):
        """Ensure the session is closed when the object is destroyed"""
        if hasattr(self, 'session') and self.session:
            self.session.close()

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

    def print_reading(self, reading: Reading, show_actual_dates: bool = False) -> None:
        """
        Print formatted reading information
        Args:
            reading: Reading object to print
            show_actual_dates: If True, shows actual dates instead of estimated dates
        """
        # For start date, use actual if available, otherwise use estimated
        start_date = (reading.date_started.strftime('%Y-%m-%d') if reading.date_started 
                     else (reading.date_est_start.strftime('%Y-%m-%d') if reading.date_est_start 
                           else 'Not scheduled'))
        
        # For end date, use actual if available, otherwise use estimated
        end_date = (reading.date_finished_actual.strftime('%Y-%m-%d') if reading.date_finished_actual 
                    else (reading.date_est_end.strftime('%Y-%m-%d') if reading.date_est_end 
                          else 'Not scheduled'))
        
        # Construct author name from first and second name fields
        author_parts = [
            reading.book.author_name_first,
            reading.book.author_name_second
        ]
        author = " ".join(filter(None, author_parts)) or 'Unknown Author'
        
        # Get media color
        media_color = self._get_media_color(reading.media)
        
        self.console.print(
            f"[bold]{reading.book.title}[/bold] by {author}\n"
            f"Start: {start_date} | End: {end_date}\n"
            f"Media: [{media_color}]{reading.media}[/{media_color}] | "
            f"Reading ID: {reading.id} | Previous ID: {reading.id_previous or 'None'}"
        )

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
                self.session.query(Reading)
                .join(Book)
            )

            if exact_match:
                query = query.filter(Book.title == title)
            else:
                query = query.filter(Book.title.ilike(f"%{title}%"))

            results = query.all()

            if not results:
                self.console.print(f"\n[yellow]No readings found for book title: '{title}'[/yellow]")
                return []

            return results

        except Exception as e:
            self.console.print(f"\n[red]Error executing query: {e}[/red]")
            return []

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

    def get_reading_chain(self, reading_id: int) -> list:
        """
        Get all readings in a chain containing the specified reading ID.
        Returns the complete chain from start to end.
        """
        try:
            # Get the initial reading
            current = self.session.get(Reading, reading_id)
            if not current:
                return []

            chain = []
            
            # First, go backwards to find the start of the chain
            while current and current.id_previous:
                current = self.session.get(Reading, current.id_previous)
            
            # Now traverse forward through the chain
            while current:
                chain.append(current)
                next_reading = (self.session.query(Reading)
                              .filter(Reading.id_previous == current.id)
                              .first())
                if not next_reading:
                    break
                current = next_reading

            return chain

        except Exception as e:
            self.console.print(f"\n[red]Error getting reading chain: {e}[/red]")
            return []

    def get_reading_details(self, reading_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific reading session.
        
        Args:
            reading_id: ID of the reading to inspect
        
        Returns:
            Dictionary containing reading details or None if not found
        """
        try:
            reading = self.session.get(Reading, reading_id)
            if not reading:
                return None
            
            # Get next reading (if any points to this one)
            next_reading = (self.session.query(Reading)
                           .filter(Reading.id_previous == reading_id)
                           .first())
            
            return {
                'reading_id': reading.id,
                'book': {
                    'id': reading.book.id,
                    'title': reading.book.title,
                    'author_first': reading.book.author_name_first,
                    'author_second': reading.book.author_name_second,
                },
                'media': reading.media,
                'dates': {
                    'started': reading.date_started,
                    'finished': reading.date_finished_actual,
                    'estimated_start': reading.date_est_start,
                    'estimated_end': reading.date_est_end,
                },
                'chain': {
                    'previous_id': reading.id_previous,
                    'next_id': next_reading.id if next_reading else None,
                    'next_title': next_reading.book.title if next_reading else None,
                },
                'progress': {
                    'days_elapsed': reading.days_elapsed_to_read,
                    'days_estimate': reading.days_estimate,
                    'days_delta': reading.days_to_read_delta_from_estimate
                }
            }
        except Exception as e:
            self.console.print(f"[red]Error retrieving reading details: {e}[/red]")
            return None

    def get_reread_books(self, reread_type: str = 'upcoming') -> list:
        """
        Get list of books that are rereads.
        
        Args:
            reread_type: Either 'upcoming' or 'finished'
                - 'upcoming': Books that have been read before and are in the current chain
                - 'finished': Books that have been completely read multiple times
        
        Returns:
            List of Reading objects that are rereads
        """
        try:
            if reread_type == 'upcoming':
                # Books that have been read before and are in current chain
                query = (
                    self.session.query(Reading)
                    .join(Book)
                    .filter(
                        Reading.date_est_end.isnot(None),
                        Reading.date_finished_actual.is_(None),
                        Book.id.in_(
                            self.session.query(Reading.book_id)
                            .filter(Reading.date_finished_actual.isnot(None))
                            .subquery()
                        )
                    )
                )
            elif reread_type == 'finished':
                # Books that have been completely read multiple times
                query = (
                    self.session.query(
                        Reading,
                        func.count(Reading.id).label('times_read')
                    )
                    .join(Book)
                    .filter(Reading.date_finished_actual.isnot(None))
                    .group_by(Reading.book_id)
                    .having(func.count(Reading.id) > 1)
                )
            else:
                raise ValueError("reread_type must be either 'upcoming' or 'finished'")
            
            results = query.all()
            
            if not results:
                self.console.print(f"\n[yellow]No {reread_type} rereads found[/yellow]")
                return []
                
            return results

        except Exception as e:
            self.console.print(f"\n[red]Error finding {reread_type} rereads: {e}[/red]")
            return []
