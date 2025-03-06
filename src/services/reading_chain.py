from typing import List, Dict, Any
from src.database import get_db

class ReadingChainService:
    def __init__(self):
        self.db = get_db()

    def get_all_chains_with_books(self) -> List[Dict[str, Any]]:
        """Get all reading chains with their books"""
        chains = []
        for media_type in ['Kindle', 'Hardcover', 'Audio']:
            books = self.get_books_for_media(media_type)
            chain = {
                'media': media_type,
                'total_books': len(books),
                'total_pages': sum(b['pages'] or 0 for b in books),
                'completion_rate': self._calculate_completion_rate(books),
                'books': books
            }
            chains.append(chain)
        return chains

    def get_books_for_media(self, media_type: str) -> List[Dict[str, Any]]:
        """Get books for specific media type"""
        # Simple count query first
        count_query = f"""
            SELECT COUNT(*) 
            FROM books b
            JOIN inv i ON b.id = i.book_id
            WHERE i.owned_{media_type.lower()} = TRUE
        """
        total_count = self.db.execute(count_query).scalar()
        print(f"\n=== {media_type} Books ===")
        print(f"Total in database: {total_count}")

        query = """
            SELECT
                b.id,
                b.title,
                b.author_name_first,
                b.author_name_second,
                b.page_count as pages,
                r.rank as priority,
                r.date_started,
                r.date_finished_actual,
                r.date_est_end as date_estimated_completion,
                CASE
                    WHEN r.date_finished_actual IS NOT NULL THEN 100
                    WHEN r.days_elapsed_to_read IS NOT NULL THEN 
                        (r.days_elapsed_to_read * 100.0 / NULLIF(r.days_estimate, 0))
                    ELSE 0
                END as progress,
                CASE
                    WHEN r.date_started IS NOT NULL AND r.date_finished_actual IS NULL THEN 'current'
                    WHEN r.date_finished_actual IS NOT NULL THEN 'completed'
                    ELSE 'upcoming'
                END as status
            FROM books b
            JOIN inv i ON b.id = i.book_id
            LEFT JOIN read r ON b.id = r.book_id
            WHERE i.owned_{} = TRUE
            ORDER BY r.rank DESC NULLS LAST, r.date_started DESC NULLS LAST
        """.format(media_type.lower())
        
        results = self.db.execute(query).fetchall()
        
        # Format books without the 11-book limit
        formatted_books = []
        for row in results:
            book = self._format_book(dict(row))
            formatted_books.append(book)
        
        return formatted_books

    def get_total_books(self) -> int:
        """Get total number of books"""
        return self.db.execute(
            "SELECT COUNT(*) FROM books"
        ).scalar()

    def get_books_count(self, media_type: str) -> int:
        """Get number of books for specific media type"""
        return self.db.execute(
            f"SELECT COUNT(*) FROM inventory WHERE owned_{media_type.lower()} = TRUE"
        ).scalar()

    def _calculate_completion_rate(self, books: List[Dict[str, Any]]) -> float:
        """Calculate completion rate for a list of books"""
        if not books:
            return 0.0
        completed = sum(1 for b in books if b['progress'] == 100)
        return round((completed / len(books)) * 100, 1)

    def _format_book(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Format book data for template"""
        formatted = {
            'book_id': row['id'],
            'title': row['title'],
            'author': f"{row['author_name_first']} {row['author_name_second']}".strip(),
            'pages': row['pages'],
            'progress': row['progress'],
            'is_current': row['status'] == 'current',
            'priority': row['priority'],
            'date_started': row['date_started'],
            'date_est_end': row['date_estimated_completion']
        }
        print(f"Formatting book: {formatted['title']}")  # Debug print
        return formatted
