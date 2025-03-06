"""Core analytics functionality for reading reports."""
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta, date, timedelta
from sqlalchemy import extract, text
from ..models.base import SessionLocal
from ..models.reading import Reading
from ..models.book import Book

@dataclass
class ReadingStats:
    total_books: int
    total_pages: int
    total_words: int
    average_pages_per_day: float
    average_words_per_day: float
    completion_rate: float

class ReadingAnalytics:
    """Core analytics class for reading statistics and visualizations"""
    
    def __init__(self):
        self.session = SessionLocal()

    def get_reading_summary(self, year: Optional[int] = None) -> Dict:
        """Get overall reading statistics"""
        where_clause = f"WHERE strftime('%Y', r.date_finished_actual) = '{year}'" if year else ""
        
        query = f"""
            SELECT 
                COUNT(DISTINCT r.book_id) as total_books,
                SUM(b.word_count) as total_words,
                SUM(b.page_count) as total_pages,
                COUNT(DISTINCT b.author_name_first || ' ' || b.author_name_second) as unique_authors,
                COUNT(DISTINCT b.series) as unique_series
            FROM read r
            JOIN books b ON r.book_id = b.id
            {where_clause}
        """
        with self.session.connect() as conn:
            result = conn.execute(text(query)).fetchone()
            
        return {
            'total_books': result[0],
            'total_words': result[1],
            'total_pages': result[2],
            'unique_authors': result[3],
            'unique_series': result[4]
        }

    def get_reading_trends(self) -> "pd.DataFrame":
        """Get monthly reading trends"""
        query = """
            SELECT 
                strftime('%Y-%m', r.date_finished_actual) as month,
                COUNT(DISTINCT r.book_id) as books_read,
                SUM(b.word_count) as words_read,
                SUM(b.page_count) as pages_read
            FROM read r
            JOIN books b ON r.book_id = b.id
            GROUP BY strftime('%Y-%m', r.date_finished_actual)
            ORDER BY month
        """
        return pd.read_sql(query, self.session.bind)

    def get_projected_readings(self, year: int) -> List[Dict]:
        """
        Get projected readings for a specific year.
        Returns list of books with projected completion dates.
        """
        query = """
            SELECT
                strftime('%m', COALESCE(r.date_finished_actual, r.date_est_end)) as month,
                b.id,
                b.title,
                b.author_name_first,
                b.author_name_second,
                b.page_count,
                b.word_count,
                r.media,
                date(r.date_started) as date_started,
                date(r.date_finished_actual) as date_finished_actual,
                date(r.date_est_end) as date_est_end
            FROM read r
            JOIN books b ON r.book_id = b.id
            WHERE strftime('%Y', COALESCE(r.date_finished_actual, r.date_est_end)) = :year
            ORDER BY COALESCE(r.date_finished_actual, r.date_est_end)
        """
        with self.session.connect() as conn:
            result = conn.execute(text(query), {"year": str(year)}).fetchall()
        return result

    def process_readings_data(self, readings):
        """Process raw readings data into a format suitable for the template"""
        months_data = {}

        # Initialize all months with zero values
        for month in range(1, 13):
            months_data[month] = {
                'books': [],
                'total_books': 0,
                'total_pages': 0,
                'total_words': 0
            }

        for reading in readings:
            month = int(reading.month)
            # Convert string dates to datetime objects if they're not None
            est_end = datetime.strptime(reading.date_est_end, '%Y-%m-%d').date() if reading.date_est_end else None
            started = datetime.strptime(reading.date_started, '%Y-%m-%d').date() if reading.date_started else None
            finished = datetime.strptime(reading.date_finished_actual, '%Y-%m-%d').date() if reading.date_finished_actual else None

            book_data = {
                'id': reading.id,
                'title': reading.title,
                'author': self.format_author_name(reading.author_name_first, reading.author_name_second),
                'pages': int(reading.page_count or 0),
                'words': int(reading.word_count or 0),
                'media': reading.media or 'Unknown',
                'started': started,
                'finished': finished,
                'est_end': est_end
            }

            months_data[month]['books'].append(book_data)
            months_data[month]['total_books'] += 1
            months_data[month]['total_pages'] += book_data['pages']
            months_data[month]['total_words'] += book_data['words']

        return months_data

    def calculate_cumulative_stats(self, months_data):
        """Calculate cumulative statistics from monthly data"""
        cumulative_books = []
        cumulative_words = []
        cumulative_pages = []
        running_books = 0
        running_words = 0
        running_pages = 0

        for m in range(1, 13):
            running_books += months_data[m]['total_books']
            running_words += months_data[m]['total_words']
            running_pages += months_data[m]['total_pages']
            cumulative_books.append(running_books)
            cumulative_words.append(running_words)
            cumulative_pages.append(running_pages)

        return cumulative_books, cumulative_words, cumulative_pages

    @staticmethod
    def format_author_name(first, second):
        """Format author's full name"""
        return f"{first or ''} {second or ''}".strip() or "Unknown Author"

class AuthorAnalytics:
    """Analytics specific to author statistics"""
    
    def __init__(self):
        self.engine = engine

    def get_top_authors(self, limit: int = 10) -> pd.DataFrame:
        """Get most read authors by book count and word count"""
        query = """
            SELECT 
                b.author_name_first || ' ' || b.author_name_second as author,
                COUNT(DISTINCT r.book_id) as books_read,
                SUM(b.word_count) as total_words,
                SUM(b.page_count) as total_pages
            FROM read r
            JOIN books b ON r.book_id = b.id
            GROUP BY b.author_name_first, b.author_name_second
            ORDER BY books_read DESC
            LIMIT :limit
        """
        return pd.read_sql(text(query), self.engine, params={'limit': limit})

class SeriesAnalytics:
    """Analytics specific to book series"""
    
    def __init__(self):
        self.engine = engine

    def get_series_completion(self) -> pd.DataFrame:
        """Get completion status of different series"""
        query = """
            SELECT 
                b.series,
                COUNT(DISTINCT b.id) as total_books,
                COUNT(DISTINCT r.book_id) as books_read,
                SUM(b.word_count) as total_words
            FROM books b
            LEFT JOIN read r ON b.id = r.book_id
            WHERE b.series IS NOT NULL
            GROUP BY b.series
            ORDER BY total_books DESC
        """
        return pd.read_sql(query, self.engine)

class TimeAnalytics:
    """Analytics for time-based reading patterns"""
    
    def __init__(self):
        self.engine = engine

    def get_reading_velocity(self, window: str = 'monthly') -> pd.DataFrame:
        """Get reading velocity (books/words per time period)"""
        group_by = "strftime('%Y-%m', r.date_finished_actual)" if window == 'monthly' else "strftime('%Y', r.date_finished_actual)"
        
        query = f"""
            SELECT 
                {group_by} as period,
                COUNT(DISTINCT r.book_id) / COUNT(DISTINCT strftime('%Y-%m-%d', r.date_finished_actual)) as books_per_day,
                SUM(b.word_count) / COUNT(DISTINCT strftime('%Y-%m-%d', r.date_finished_actual)) as words_per_day
            FROM read r
            JOIN books b ON r.book_id = b.id
            GROUP BY {group_by}
            ORDER BY period
        """
        return pd.read_sql(query, self.engine)

class ReportAnalytics:
    """Analytics specifically for generating reading reports"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

    def get_yearly_readings(self, year: int, actual_only: bool = False, estimated_only: bool = False) -> List[Dict]:
        """Get readings for a specific year with complete book information."""
        where_clause = f"WHERE strftime('%Y', COALESCE(r.date_finished_actual, r.date_est_end)) = :year"
        if actual_only:
            where_clause += " AND r.date_finished_actual IS NOT NULL"
        elif estimated_only:
            where_clause += " AND r.date_finished_actual IS NULL"
        
        query = f"""
            SELECT 
                strftime('%m', COALESCE(r.date_finished_actual, r.date_est_end)) as month,
                b.id as book_id,
                b.title,
                b.author_name_first || ' ' || b.author_name_second as author,
                COALESCE(b.page_count, 0) as pages,
                COALESCE(b.word_count, 0) as words,
                r.media as format,
                date(r.date_started) as start_date,
                date(r.date_finished_actual) as end_date,
                CASE 
                    WHEN r.date_finished_actual IS NOT NULL THEN 'completed'
                    ELSE 'projected'
                END as status
            FROM read r
            JOIN books b ON r.book_id = b.id
            {where_clause}
            ORDER BY COALESCE(r.date_finished_actual, r.date_est_end)
        """
        
        result = self.session.execute(text(query), {"year": str(year)})
        readings = []
        
        for row in result.fetchall():  # Use fetchall() to get all rows at once
            reading_dict = {
                'month': int(row.month) if row.month else 0,
                'book_id': row.book_id,
                'title': row.title,
                'author': row.author,
                'pages': int(row.pages or 0),
                'words': int(row.words or 0),
                'format': row.format,
                'start_date': row.start_date,
                'end_date': row.end_date,
                'status': row.status
            }
            readings.append(reading_dict)
        
        return readings

    def get_projected_readings(self, year: int) -> List[Dict[str, Any]]:
        """Get projected readings for a specific year."""
        readings = (
            self.session.query(Reading, Book)
            .join(Book)
            .filter(
                extract('year', Reading.date_est_end) == year,
                Reading.date_finished_actual.is_(None)
            )
            .order_by(Reading.date_est_end)
            .all()
        )

        return [
            {
                'book_id': book.id,
                'title': book.title,
                'author_name_first': book.author_name_first,
                'author_name_second': book.author_name_second,
                'page_count': book.page_count,
                'word_count': book.word_count,
                'month': reading.date_est_end.month,
                'date_est_end': reading.date_est_end
            }
            for reading, book in readings
        ]

    def process_readings_data(self, readings: List[Dict]) -> Dict:
        """Process readings data into monthly statistics."""
        months_data = {
            month: {
                'books': [],
                'total_books': 0,
                'total_pages': 0,
                'total_words': 0
            }
            for month in range(1, 13)
        }

        # Track unique books per month to avoid double counting
        seen_books = set()
        
        for reading in readings:
            month = int(reading['month'])
            book_id = reading['book_id']
            
            # Only count each book once per month
            month_key = (month, book_id)
            if month_key not in seen_books:
                seen_books.add(month_key)
                months_data[month]['books'].append(reading)
                months_data[month]['total_books'] += 1
                months_data[month]['total_pages'] += reading['pages']
                months_data[month]['total_words'] += reading['words']

        return months_data

    def calculate_cumulative_stats(self, months_data: Dict) -> tuple:
        """Calculate cumulative statistics by month."""
        cumulative_books = []
        cumulative_words = []
        cumulative_pages = []
        
        running_books = running_words = running_pages = 0
        
        for month in range(1, 13):
            if month in months_data:
                running_books += months_data[month]['total_books']
                running_words += months_data[month]['total_words']
                running_pages += months_data[month]['total_pages']
            
            cumulative_books.append(running_books)
            cumulative_words.append(running_words)
            cumulative_pages.append(running_pages)
        
        return cumulative_books, cumulative_words, cumulative_pages

    def get_reading_stats(self, start_date: date, end_date: date) -> ReadingStats:
        """
        Calculate reading statistics for a given date range.
        """
        readings = self._get_readings_in_range(start_date, end_date)
        
        total_books = len(readings)
        total_pages = sum(r['pages'] or 0 for r in readings)
        total_words = sum(r['words'] or 0 for r in readings)
        
        days = (end_date - start_date).days + 1
        avg_pages = total_pages / days if days > 0 else 0
        avg_words = total_words / days if days > 0 else 0
        
        completed_books = len([r for r in readings if r['completed']])
        completion_rate = (completed_books / total_books) if total_books > 0 else 0

        return ReadingStats(
            total_books=total_books,
            total_pages=total_pages,
            total_words=total_words,
            average_pages_per_day=avg_pages,
            average_words_per_day=avg_words,
            completion_rate=completion_rate
        )

    def get_reading_pace(self, reading_id: int) -> Optional[float]:
        """
        Calculate current reading pace (pages per day) for a specific reading.
        """
        with self.session_scope() as session:
            reading = self._get_reading(session, reading_id)
            if not reading or not reading['start_date']:
                return None

            days_reading = (date.today() - reading['start_date']).days
            if days_reading <= 0:
                return None

            pages_read = reading['pages_read'] or 0
            return pages_read / days_reading

    def _initialize_month_data(self) -> Dict:
        """Initialize data structure for monthly statistics."""
        return {
            'books': [],
            'total_books': 0,
            'total_pages': 0,
            'total_words': 0
        }

    def _format_reading(self, reading, book) -> Dict:
        """Format reading and book data into a consistent dictionary."""
        return {
            'id': reading.id,
            'title': book.title,
            'author': book.author,
            'pages': book.pages,
            'words': book.word_count,
            'start_date': reading.start_date,
            'end_date': reading.end_date,
            'est_end': self._calculate_estimated_completion(reading, book),
            'completed': reading.completed,
            'pages_read': reading.pages_read
        }

    def _calculate_estimated_completion(self, reading, book) -> Optional[date]:
        """Calculate estimated completion date based on current reading pace."""
        if not reading.start_date or not book.pages:
            return None

        if reading.pages_read is None:
            return None

        current_pace = self.get_reading_pace(reading.id)
        if not current_pace or current_pace <= 0:
            return None

        remaining_pages = book.pages - (reading.pages_read or 0)
        days_remaining = remaining_pages / current_pace
        
        return date.today() + timedelta(days=days_remaining)

    def _get_projected_completion_month(self, reading: Dict) -> Optional[int]:
        """Get the month number (1-12) when a reading is projected to complete."""
        if reading['completed']:
            return reading['end_date'].month if reading['end_date'] else None
        
        est_end = reading['est_end']
        return est_end.month if est_end else None

    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        from contextlib import contextmanager
        from ..models.base import SessionLocal

        @contextmanager
        def scope():
            session = SessionLocal()
            try:
                yield session
                session.commit()
            except:
                session.rollback()
                raise
            finally:
                session.close()

        return scope()
