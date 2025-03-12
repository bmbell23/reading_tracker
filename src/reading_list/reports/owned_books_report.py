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
            
            # First, collect series publication dates
            series_latest_dates = {}  # Dictionary to store latest publication date for each series
            for format_type in ['physical', 'kindle', 'audio']:
                for book in all_books.get(format_type, []):
                    series = book.get('series')
                    pub_date = book.get('date_published')
                    
                    if series and pub_date:
                        current_latest = series_latest_dates.get(series)
                        if not current_latest or pub_date > current_latest:
                            series_latest_dates[series] = pub_date

            # Process books
            books_by_id = {}  # Dictionary to track unique books
            total_books = 0
            total_read = 0
            total_pages = 0
            total_words = 0

            # Track format-specific stats
            format_stats = {
                'physical': {'total': 0, 'read': 0},
                'kindle': {'total': 0, 'read': 0},
                'audio': {'total': 0, 'read': 0}
            }

            # Process all formats
            for format_type in ['physical', 'kindle', 'audio']:
                for book in all_books.get(format_type, []):
                    book_id = book['book_id']
                    
                    # Update format-specific stats
                    format_stats[format_type]['total'] += 1
                    if book['reading_status'] == 'completed':
                        format_stats[format_type]['read'] += 1

                    if book_id not in books_by_id:
                        total_books += 1
                        total_pages += book['pages'] or 0
                        total_words += book['words'] or 0
                        
                        # Get the effective publication date
                        pub_date = book['date_published']
                        series = book['series']
                        effective_pub_date = series_latest_dates.get(series, pub_date) if series else pub_date
                        
                        books_by_id[book_id] = {
                            'title': book['title'],
                            'author': book['author'],
                            'series': series,
                            'series_number': float(book['series_index'] or 0),
                            'publication_date': pub_date,
                            'effective_pub_date': effective_pub_date,  # For sorting
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
            
            # Sort books: 
            # 1. by author
            # 2. by effective publication date (latest series date for series books)
            # 3. by series name
            # 4. by series number
            # 5. by title
            processed_books.sort(key=lambda x: (
                x['author'],
                x['effective_pub_date'] or date.max,  # Handle None dates
                x['series'] or 'zzzz',  # Put non-series books last within their publication date group
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
                total_words=total_words,
                format_stats=format_stats
            )

            # Write the report
            reports_dir = self.project_paths['reports'] / 'chain'
            reports_dir.mkdir(parents=True, exist_ok=True)
            output_path = reports_dir / 'owned_books.html'
            output_path.write_text(html)

            return str(output_path), True

        except Exception as e:
            return f"Error generating report: {str(e)}", False