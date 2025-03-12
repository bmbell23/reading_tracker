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
        """Generate the owned books report."""
        try:
            # Get all books
            all_books = self.queries.get_all_owned_books()
            
            # Process books
            books_by_id = {}  # Dictionary to track unique books
            total_books = 0
            total_read = 0
            total_pages = 0
            total_words = 0

            # Process all formats
            for format_type in ['physical', 'kindle', 'audio']:
                for book in all_books.get(format_type, []):
                    book_id = book['book_id']
                    
                    if book_id not in books_by_id:
                        total_books += 1
                        total_pages += book['pages'] or 0
                        total_words += book['words'] or 0
                        
                        books_by_id[book_id] = {
                            'title': book['title'],
                            'author': book['author'],
                            'series': book['series'],
                            'series_number': float(book['series_index'] or 0),  # Convert to float for proper sorting
                            'formats': [],
                            'cover_url': self.get_book_cover_path(book_id) or '/assets/images/no-cover.jpg',
                            'book_id': book_id,
                            'is_read': False
                        }

                    books_by_id[book_id]['formats'].append({
                        'type': format_type,
                        'status': book['reading_status'],
                        'reading_id': book['reading_id']
                    })
                    
                    if book['reading_status'] == 'completed' and not books_by_id[book_id]['is_read']:
                        books_by_id[book_id]['is_read'] = True
                        total_read += 1

            # Convert dictionary to list and sort
            processed_books = list(books_by_id.values())
            
            # Sort books: first by author, then by series, then by series number, then by title
            processed_books.sort(key=lambda x: (
                x['author'],
                x['series'] or 'zzzz',  # Put non-series books last
                x['series_number'],
                x['title']
            ))

            # Set up Jinja2 environment and render
            template_dir = self.project_paths['templates'] / 'reports' / 'owned'
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('owned_books_report.html')

            html = template.render(
                books=processed_books,
                total_books=total_books,
                total_read=total_read,
                total_pages=total_pages,
                total_words=total_words
            )

            # Write the report
            reports_dir = self.project_paths['reports'] / 'chain'
            reports_dir.mkdir(parents=True, exist_ok=True)
            output_path = reports_dir / 'owned_books.html'
            output_path.write_text(html)

            return str(output_path), True

        except Exception as e:
            return f"Error generating report: {str(e)}", False