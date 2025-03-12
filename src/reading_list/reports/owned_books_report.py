from pathlib import Path
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from ..queries.common_queries import CommonQueries
from ..utils.paths import get_project_paths

class OwnedBooksReport:
    def __init__(self):
        self.queries = CommonQueries()
        self.project_paths = get_project_paths()
        self.covers_dir = self.project_paths['workspace'] / 'assets' / 'book_covers'

    def get_book_cover_path(self, book_id: int) -> str:
        """Get the relative path to the book cover image"""
        if not book_id:
            return None

        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            cover_path = self.covers_dir / f"{book_id}{ext}"
            if cover_path.exists():
                return f"/assets/book_covers/{book_id}{ext}"
        return None

    def generate_report(self) -> tuple[str, bool]:
        """Generate the owned books report.
        
        Returns:
            Tuple of (output_path, success)
        """
        try:
            # Get all books
            all_books = self.queries.get_all_owned_books()
            
            # Process books
            processed_books = []
            total_books = 0
            total_read = 0
            total_pages = 0
            total_words = 0

            for format_type in ['physical', 'kindle', 'audio']:
                for book in all_books.get(format_type, []):
                    total_books += 1
                    if book['reading_status'] == 'completed':
                        total_read += 1
                    total_pages += book['pages'] or 0
                    total_words += book['words'] or 0

                    processed_books.append({
                        'title': book['title'],
                        'author': book['author'],
                        'format': format_type,
                        'status': book['reading_status'],
                        'cover_url': self.get_book_cover_path(book['book_id']) or '/assets/images/no-cover.jpg',
                        'book_id': book['book_id'],
                        'reading_id': book['reading_id']
                    })

            # Sort books by author, then title
            processed_books.sort(key=lambda x: (x['author'], x['title']))

            # Set up Jinja2 environment
            template_dir = self.project_paths['templates'] / 'reports' / 'owned'
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('owned_books_report.html')

            # Generate HTML
            html = template.render(
                books=processed_books,
                total_books=total_books,
                total_read=total_read,
                total_pages=total_pages,
                total_words=total_words
            )

            # Write the report
            reports_dir = self.project_paths['reports'] / 'owned'
            reports_dir.mkdir(parents=True, exist_ok=True)
            output_path = reports_dir / 'owned_books.html'
            output_path.write_text(html)

            return str(output_path), True

        except Exception as e:
            return f"Error generating report: {str(e)}", False