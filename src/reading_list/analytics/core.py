from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy import text
from src.models.base import engine

class ReadingAnalytics:
    """Core analytics class for reading statistics and visualizations"""
    
    def __init__(self):
        self.engine = engine

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
        with self.engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
            
        return {
            'total_books': result[0],
            'total_words': result[1],
            'total_pages': result[2],
            'unique_authors': result[3],
            'unique_series': result[4]
        }

    def get_reading_trends(self) -> pd.DataFrame:
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
        return pd.read_sql(query, self.engine)

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