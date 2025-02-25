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
        query = """
            SELECT
                b.id_book,
                b.title,
                b.author_name_first,
                b.author_name_second,
                b.page_count as pages,
                r.priority,
                r.date_started,
                r.date_finished_actual,
                r.date_finished_estimate as date_estimated_completion,
                CASE
                    WHEN r.date_finished_actual IS NOT NULL THEN 100
                    WHEN r.progress IS NOT NULL THEN r.progress
                    ELSE 0
                END as progress,
                CASE
                    WHEN r.date_started IS NOT NULL AND r.date_finished_actual IS NULL THEN 'current'
                    WHEN r.date_finished_actual IS NOT NULL THEN 'completed'
                    ELSE 'upcoming'
                END as status
            FROM books b
            JOIN readings r ON b.id_book = r.id_book
            JOIN inventory i ON b.id_book = i.id_book
            WHERE i.owned_{} = TRUE
            ORDER BY r.priority DESC, r.date_started DESC
        """.format(media_type.lower())

        results = self.db.execute(query).fetchall()
        return [self._format_book(dict(row)) for row in results]

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
        return {
            'id': row['id_book'],
            'title': row['title'],
            'author': f"{row['author_name_first']} {row['author_name_second']}".strip(),
            'pages': row['pages'],
            'progress': row['progress'],
            'current': row['status'] == 'current',
            'priority': row['priority'],
            'date_started': row['date_started'],
            'date_est_end': row['date_estimated_completion']
        }
