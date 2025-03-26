from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from ..models.reading import Reading
from ..models.book import Book
from ..models.base import SessionLocal
from rich.console import Console
from sqlalchemy import func, text

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
            f"Reading ID: {reading.id} | Book ID: {reading.book.id} | Previous ID: {reading.id_previous or 'None'}"
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

    def get_reading_chain(self, reading_id: int) -> List[Reading]:
        """
        Get a complete reading chain containing the specified reading.
        Includes readings both before and after the specified reading.
        """
        # First get the reading
        reading = self.session.get(Reading, reading_id)
        if not reading:
            return []

        chain = []

        # Get all previous readings
        current = reading
        while current.id_previous is not None:
            prev_reading = self.session.get(Reading, current.id_previous)
            if prev_reading:
                chain.insert(0, prev_reading)
                current = prev_reading
            else:
                break

        # Add the current reading
        chain.append(reading)

        # Get all next readings
        current = reading
        while True:
            next_reading = (self.session.query(Reading)
                           .filter(Reading.id_previous == current.id)
                           .first())
            if next_reading:
                chain.append(next_reading)
                current = next_reading
            else:
                break

        return chain

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
                # Get IDs of books that have been finished at least once
                finished_book_ids = (
                    self.session.query(Reading.book_id)
                    .filter(Reading.date_finished_actual.isnot(None))
                    .distinct()
                )

                # Main query to get upcoming readings of previously read books
                query = (
                    self.session.query(Reading)
                    .join(Book)
                    .filter(
                        Reading.date_est_end.isnot(None),
                        Reading.date_finished_actual.is_(None),
                        Reading.book_id.in_(finished_book_ids)
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

    def get_all_readings_ordered_by_start(self) -> List[Dict[str, Any]]:
        """
        Get all readings ordered by start date (actual or estimated)
        Returns a list of readings with basic book info, ordered by start date
        """
        query = """
            SELECT
                r.id,
                r.date_started,
                r.date_est_start,
                b.title,
                b.id as book_id,
                r.media
            FROM read r
            JOIN books b ON r.book_id = b.id
            ORDER BY COALESCE(date_started, date_est_start)
        """

        try:
            results = self.session.execute(text(query)).fetchall()
            return [dict(row._mapping) for row in results]
        except Exception as e:
            self.console.print(f"\n[red]Error getting readings: {e}[/red]")
            return []

    def get_book_cover_path(self, book_id: int) -> Optional[str]:
        """Get the path to a book's cover image"""
        from reading_list.utils.paths import get_project_paths

        project_paths = get_project_paths()
        covers_dir = project_paths['workspace'] / 'data' / 'covers'

        # Check for cover file with different extensions
        for ext in ['.jpg', '.jpeg', '.png']:
            cover_path = covers_dir / f"{book_id}{ext}"
            if cover_path.exists():
                return str(cover_path.relative_to(project_paths['workspace']))
        return None

    def format_date(self, date_value) -> Optional[str]:
        """Format date value, handling both datetime/date objects and strings"""
        if not date_value:
            return None
        if isinstance(date_value, str):
            return date_value
        return date_value.strftime('%Y-%m-%d')

    def get_reading_chain_by_media(self, media_type: str) -> List[Dict[str, Any]]:
        """
        Get a reading chain for a specific media type.

        Args:
            media_type: Type of media (kindle, hardcover, audio)

        Returns:
            List of readings in the chain for that media type
        """
        try:
            # Get all readings for this media type that are either:
            # 1. Currently being read (started but not finished)
            # 2. Scheduled for the future (have estimated dates but not started)
            readings = (
                self.session.query(Reading)
                .join(Book)
                .filter(
                    Reading.media.ilike(media_type),
                    Reading.date_finished_actual.is_(None)
                )
                .order_by(Reading.date_est_start)
                .all()
            )

            chain_data = []
            for reading in readings:
                # Format dates
                date_started = self.format_date(reading.date_started)
                date_est_start = self.format_date(reading.date_est_start)
                date_est_end = self.format_date(reading.date_est_end)

                # Determine if reading is current or future
                is_current = reading.date_started is not None and reading.date_finished_actual is None
                is_future = reading.date_started is None

                # Get cover path
                cover_path = self.get_book_cover_path(reading.book.id)

                chain_data.append({
                    'id': reading.id,
                    'title': reading.book.title,
                    'author_name_first': reading.book.author_name_first,
                    'author_name_second': reading.book.author_name_second,
                    'media': reading.media,
                    'date_started': date_started,
                    'date_est_start': date_est_start,
                    'date_est_end': date_est_end,
                    'cover_path': cover_path,
                    'is_current': is_current,
                    'is_future': is_future,
                    'id_previous': reading.id_previous
                })

            return chain_data

        except Exception as e:
            self.console.print(f"[red]Error getting {media_type} chain: {str(e)}[/red]")
            return []

    def get_reading_chain_by_media(self, media: str) -> List[Dict]:
        """
        Get all readings in a chain for a specific media type.

        Args:
            media: Media type to filter by (e.g., 'Audio', 'Kindle', etc.)

        Returns:
            List of dictionaries containing reading information
        """
        try:
            query = """
                WITH RECURSIVE chain AS (
                    -- Get all readings without a previous reading (chain starts)
                    SELECT
                        r.id as read_id,
                        r.media,
                        r.id_previous,
                        b.title,
                        b.author_name_first,
                        b.author_name_second,
                        r.date_est_start,
                        1 as chain_order
                    FROM read r
                    JOIN books b ON r.book_id = b.id
                    WHERE r.media = :media
                    AND r.id_previous IS NULL

                    UNION ALL

                    -- Get all subsequent readings in the chain
                    SELECT
                        r.id,
                        r.media,
                        r.id_previous,
                        b.title,
                        b.author_name_first,
                        b.author_name_second,
                        r.date_est_start,
                        c.chain_order + 1
                    FROM read r
                    JOIN books b ON r.book_id = b.id
                    JOIN chain c ON r.id_previous = c.read_id
                    WHERE r.media = :media
                )
                SELECT * FROM chain
                ORDER BY chain_order;
            """

            results = self.session.execute(text(query), {'media': media}).fetchall()

            return [
                {
                    'read_id': row.read_id,
                    'media': row.media,
                    'title': row.title,
                    'author': f"{row.author_name_first or ''} {row.author_name_second or ''}".strip(),
                    'chain': {
                        'previous_id': row.id_previous
                    }
                }
                for row in results
            ]
        except Exception as e:
            self.console.print(f"[red]Error getting reading chain: {str(e)}[/red]")
            return []

    def get_books_by_format(self, media_format: str) -> List[Dict[str, Any]]:
        """Get all books of a specific format"""
        try:
            query = """
                SELECT DISTINCT
                    b.id as book_id,
                    b.title,
                    b.author_name_first,
                    b.author_name_second,
                    b.page_count,
                    b.word_count,
                    b.series,
                    b.series_number,
                    b.date_published,
                    i.location,
                    r.id as reading_id,
                    r.date_started,
                    r.date_finished_actual,
                    (
                        SELECT COUNT(*)
                        FROM read r2
                        WHERE r2.book_id = b.id
                        AND r2.date_finished_actual IS NOT NULL
                    ) as times_completed,
                    (
                        SELECT MIN(r2.date_started)
                        FROM read r2
                        WHERE r2.book_id = b.id
                        AND r2.date_finished_actual IS NOT NULL
                    ) as first_read_date
                FROM books b
                JOIN inv i ON b.id = i.book_id
                LEFT JOIN read r ON b.id = r.book_id
                WHERE i.owned_{} = TRUE
                GROUP BY b.id
            """.format(media_format.lower())
            
            results = self.session.execute(text(query))
            
            return [{
                'book_id': row.book_id,
                'reading_id': row.reading_id,
                'title': row.title,
                'author': f"{row.author_name_first or ''} {row.author_name_second or ''}".strip(),
                'author_sort': f"{row.author_name_second or ''}, {row.author_name_first or ''}".strip(),
                'pages': row.page_count,
                'words': row.word_count,
                'location': row.location,
                'series': row.series,
                'series_index': row.series_number,
                'date_published': row.date_published,
                'first_read_date': row.first_read_date,
                'reading_status': ('reading' if row.date_started and not row.date_finished_actual
                                 else 'completed' if row.times_completed > 0
                                 else 'unread'),
                'reading_id': row.reading_id
            } for row in results]
        
        except Exception as e:
            self.console.print(f"[red]Error getting {media_format} books: {str(e)}[/red]")
            return []

    def get_all_owned_books(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all owned books organized by format
        
        Returns:
            Dictionary with keys 'physical', 'kindle', and 'audio', each containing
            a list of books in that format
        """
        return {
            'physical': self.get_books_by_format('physical'),
            'kindle': self.get_books_by_format('kindle'),
            'audio': self.get_books_by_format('audio')
        }

    def get_books_by_author(self) -> List[Dict[str, Any]]:
        """
        Get count of books read by each author, including both unique books and total reading sessions
        """
        query = """
            WITH book_ownership AS (
                SELECT 
                    book_id,
                    MAX(CASE WHEN owned_physical THEN 1 ELSE 0 END) as has_physical,
                    MAX(CASE WHEN owned_kindle THEN 1 ELSE 0 END) as has_kindle,
                    MAX(CASE WHEN owned_audio THEN 1 ELSE 0 END) as has_audio
                FROM inv
                GROUP BY book_id
            ),
            reading_stats AS (
                SELECT 
                    book_id,
                    COUNT(*) as total_sessions,
                    COUNT(DISTINCT book_id) as unique_books
                FROM read
                WHERE date_finished_actual IS NOT NULL
                GROUP BY book_id
            )
            SELECT 
                COALESCE(b.author_name_second || ', ' || b.author_name_first,
                        b.author_name_first || ' ' || b.author_name_second,
                        'Unknown Author') as author,
                COUNT(DISTINCT CASE WHEN bo.has_physical + bo.has_kindle + bo.has_audio > 0 
                                   THEN b.id END) as total_books_owned,
                COUNT(DISTINCT CASE WHEN r.date_finished_actual IS NOT NULL 
                                   THEN b.id END) as unique_books_completed,
                COUNT(CASE WHEN r.date_finished_actual IS NOT NULL 
                      THEN r.id END) as total_reading_sessions,
                COUNT(DISTINCT CASE WHEN (r.date_finished_actual IS NULL AND r.date_started IS NOT NULL) OR
                                   (r.date_finished_actual IS NULL AND r.date_est_start IS NOT NULL)
                               THEN b.id END) as future_reads
            FROM books b
            LEFT JOIN read r ON b.id = r.book_id
            LEFT JOIN book_ownership bo ON b.id = bo.book_id
            LEFT JOIN reading_stats rs ON b.id = rs.book_id
            WHERE r.book_id IS NOT NULL  -- Only include books that have readings
            GROUP BY 
                b.author_name_first,
                b.author_name_second
            ORDER BY total_reading_sessions DESC, unique_books_completed DESC, author ASC
        """
        
        try:
            results = self.session.execute(text(query))
            return [dict(row._mapping) for row in results]
        except Exception as e:
            self.console.print(f"\n[red]Error getting author statistics: {e}[/red]")
            return []

    def debug_author_books(self, author_first: str, author_second: str = None) -> List[Dict[str, Any]]:
        """
        Debug query to show detailed information about an author's books
        """
        query = """
            WITH book_ownership AS (
                SELECT 
                    book_id,
                    MAX(CASE WHEN owned_physical THEN 1 ELSE 0 END) as has_physical,
                    MAX(CASE WHEN owned_kindle THEN 1 ELSE 0 END) as has_kindle,
                    MAX(CASE WHEN owned_audio THEN 1 ELSE 0 END) as has_audio
                FROM inv
                GROUP BY book_id
                HAVING (has_physical + has_kindle + has_audio) > 0
            ),
            completed_readings AS (
                SELECT 
                    book_id,
                    COUNT(*) as times_completed
                FROM read
                WHERE date_finished_actual IS NOT NULL
                GROUP BY book_id
            )
            SELECT 
                b.id as book_id,
                b.title,
                bo.has_physical,
                bo.has_kindle,
                bo.has_audio,
                COALESCE(cr.times_completed, 0) as times_completed
            FROM books b
            JOIN book_ownership bo ON b.id = bo.book_id
            LEFT JOIN completed_readings cr ON b.id = cr.book_id
            WHERE b.author_name_first = :first
            AND (:second IS NULL OR b.author_name_second = :second)
            ORDER BY b.title
        """
        
        try:
            results = self.session.execute(text(query), {
                "first": author_first,
                "second": author_second
            })
            books = [dict(row._mapping) for row in results]
            
            # Print detailed report
            self.console.print("\n[bold cyan]Detailed Book Analysis (Owned Books Only)[/bold cyan]")
            for book in books:
                formats = []
                if book['has_physical']: formats.append('physical')
                if book['has_kindle']: formats.append('kindle')
                if book['has_audio']: formats.append('audio')
                
                self.console.print(
                    f"\n[bold]{book['title']}[/bold]"
                    f"\nFormats owned: {', '.join(formats)}"
                    f"\nTimes completed: {book['times_completed']}"
                )
                
            # Print summary
            total_owned = len(books)
            completed_books = len([b for b in books if b['times_completed'] > 0])
            self.console.print(
                f"\n[bold green]Summary:[/bold green]"
                f"\nTotal owned books: {total_owned}"
                f"\nOwned books with completed readings: {completed_books}"
            )
            
            return books
        except Exception as e:
            self.console.print(f"\n[red]Error in debug query: {e}[/red]")
            return []
