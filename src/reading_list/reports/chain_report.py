"""
Reading Chain Report Generator
============================

Generates reports showing the current state of reading chains.
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pathlib import Path
from sqlalchemy import text
from jinja2 import Environment, FileSystemLoader
from rich.console import Console

from ..models.base import SessionLocal
from ..models.reading import Reading
from ..models.book import Book
from ..utils.paths import get_project_paths, find_project_root, ensure_directory
from ..utils.permissions import fix_report_permissions
from ..utils.progress_calculator import calculate_reading_progress
from ..queries.common_queries import CommonQueries  # Fixed import path

console = Console()

def get_reading_chain(session, media_type: str = None) -> List[Dict[str, Any]]:
    """Get readings for a specific media type."""
    query = """
        SELECT 
            r.id,
            r.book_id,
            r.media,
            r.date_started,
            r.date_finished_actual,
            r.date_est_start,
            r.date_est_end,
            b.title,
            b.author_name_first,
            b.author_name_second,
            b.word_count,
            b.page_count
        FROM read r
        JOIN books b ON r.book_id = b.id
        WHERE (:media_type IS NULL OR r.media = :media_type)
        ORDER BY 
            COALESCE(r.date_finished_actual, r.date_started, r.date_est_start) DESC
    """
    
    result = session.execute(text(query), {"media_type": media_type})
    return [dict(zip(result.keys(), row)) for row in result]

def get_current_readings(session) -> List[Dict[str, Any]]:
    """Get all current (in-progress) readings."""
    query = """
        SELECT 
            r.id,
            r.book_id,
            r.media,
            r.date_started,
            r.date_finished_actual,
            r.date_est_start,
            r.date_est_end,
            b.title,
            b.author_name_first,
            b.author_name_second,
            b.word_count,
            b.page_count
        FROM read r
        JOIN books b ON r.book_id = b.id
        WHERE r.date_started <= CURRENT_DATE
        AND r.date_finished_actual IS NULL
        ORDER BY r.date_started DESC
    """
    
    result = session.execute(text(query))
    return [dict(zip(result.keys(), row)) for row in result]

def get_all_readings(session) -> List[Dict[str, Any]]:
    """Get all readings from the database, no chains, just readings."""
    query = """
        SELECT 
            r.id,
            r.book_id,
            r.media,
            r.date_started,
            r.date_finished_actual,
            r.date_est_start,
            r.date_est_end,
            r.reread,
            b.title,
            b.author_name_first,
            b.author_name_second,
            b.word_count,
            b.page_count
        FROM read r
        JOIN books b ON r.book_id = b.id
        ORDER BY 
            CASE WHEN r.date_finished_actual IS NOT NULL 
                THEN 1 ELSE 0 END DESC,
            r.date_finished_actual DESC,
            COALESCE(r.date_started, r.date_est_start) ASC
    """
    
    result = session.execute(text(query))
    return [dict(zip(result.keys(), row)) for row in result]

def format_author_name(first: str, second: str) -> str:
    """Format author's full name"""
    return f"{first or ''} {second or ''}".strip() or "Unknown Author"

def get_book_cover_path(book_id: int) -> str:
    """Get the relative path to the book cover image"""
    if not book_id:
        return None

    project_paths = get_project_paths()
    covers_path = project_paths['workspace'] / 'assets' / 'book_covers'

    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        cover_path = f"../../assets/book_covers/{book_id}{ext}"
        if (covers_path / f"{book_id}{ext}").exists():
            return cover_path

    return "../../assets/book_covers/0.jpg"

def format_date_with_ordinal(d: Optional[date]) -> str:
    """
    Format date as 'MMM DDst' (e.g., 'Mar 1st') or 'MMM DDst, YYYY' if not current year
    """
    if not d:
        return "Not scheduled"

    current_year = datetime.now().year

    day = d.day
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

    if d.year == current_year:
        return d.strftime(f'%b {day}{suffix}')
    else:
        return d.strftime(f'%b {day}{suffix}, %Y')

def process_reading_data(reading):
    """Process reading data for template rendering"""
    def parse_date(d):
        """Parse date string to date object"""
        return datetime.strptime(d, '%Y-%m-%d').date() if d else None

    # Parse dates
    start_date = parse_date(reading.get('date_started'))
    finished_date = parse_date(reading.get('date_finished_actual'))
    est_start = parse_date(reading.get('date_est_start'))
    est_end = parse_date(reading.get('date_est_end'))

    # A book is "current" if it has a start date but no finish date
    is_current = bool(start_date and not finished_date)

    # A book is "future" if it hasn't been started yet
    is_future = not start_date

    # Format dates with ordinal suffixes using the module-level function
    formatted_start = format_date_with_ordinal(start_date)
    formatted_finish = format_date_with_ordinal(finished_date)
    formatted_est_start = format_date_with_ordinal(est_start)
    formatted_est_end = format_date_with_ordinal(est_end)

    # Calculate progress for current books using shared calculator
    progress = "0%"
    if is_current and start_date:
        reading_obj = type('Reading', (), {
            'date_started': start_date,
            'date_est_end': est_end
        })
        progress = calculate_reading_progress(reading_obj, datetime.now().date())

    return {
        'title': reading['title'],
        'author': format_author_name(reading['author_name_first'], reading['author_name_second']),
        'date_started': formatted_start,
        'date_finished_actual': formatted_finish,
        'date_est_start': formatted_est_start,
        'date_est_end': formatted_est_end,
        'word_count': reading.get('word_count'),
        'page_count': reading.get('page_count'),
        'is_current': is_current,
        'is_future': is_future,
        'cover_url': get_book_cover_path(reading['book_id']),
        'id': reading['id'],
        'book_id': reading['book_id'],
        'media': reading['media'],
        'progress': progress,
        'reread': reading.get('reread', False)
    }

def organize_chains_by_media(readings) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Organize readings into chains by media type.

    Args:
        readings: List of reading records from database

    Returns:
        Dictionary of media types containing their reading chains
    """
    # Initialize chains structure
    chains = {
        'kindle': {'chain': []},
        'hardcover': {'chain': []},
        'audio': {'chain': []}
    }

    # Media type colors for consistent styling
    media_colors = {
        'kindle': {'text_color': '#0066CC'},     # Deeper Kindle blue
        'hardcover': {'text_color': '#6B4BA3'},  # Space purple
        'audio': {'text_color': '#FF6600'}       # Warmer Audible orange
    }

    # Group readings by media type
    for reading in readings:
        if reading.media in chains:
            reading_data = {
                'title': reading.title,
                'read_id': reading.read_id,
                'book_id': reading.book_id,
                'date_started': reading.date_started,
                'date_finished': reading.date_finished_actual,
                'media': reading.media
            }
            chains[reading.media]['chain'].append(reading_data)

    return chains

def format_date(date_value):
    """Format date value, handling both datetime objects and strings"""
    if not date_value:
        return None
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return date_value
    return date_value.strftime('%Y-%m-%d')

def generate_chain_report(args=None):
    """Generate the reading report"""
    try:
        # Get reread books
        common_queries = CommonQueries()
        reread_books = common_queries.get_reread_books(reread_type='upcoming')
        reread_book_ids = {reading.book_id for reading in reread_books}

        project_paths = get_project_paths()
        reports_dir = project_paths['workspace'] / 'reports' / 'tbr'
        output_path = reports_dir / 'to_be_read.html'
        reports_dir.mkdir(parents=True, exist_ok=True)
        ensure_directory(reports_dir)

        with SessionLocal() as session:
            # Get all readings, no chain logic
            all_readings = get_all_readings(session)
            
            # Process each reading
            all_books = []
            for reading in all_readings:
                raw_data = {
                    'title': reading['title'],
                    'author_name_first': reading['author_name_first'],
                    'author_name_second': reading['author_name_second'],
                    'date_started': reading['date_started'],
                    'date_finished_actual': reading['date_finished_actual'],
                    'date_est_start': reading['date_est_start'],
                    'date_est_end': reading['date_est_end'],
                    'word_count': reading['word_count'],
                    'page_count': reading['page_count'],
                    'book_id': reading['book_id'],
                    'id': reading['id'],
                    'media': reading['media'],
                    'reread': bool(reading['reread'])
                }

                formatted_book = process_reading_data(raw_data)
                all_books.append(formatted_book)

            # Set up Jinja2 environment
            template_dir = project_paths['templates'] / 'reports' / 'chain'
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('reading_chain_report.html')

            # Generate HTML
            html = template.render(
                books=all_books,
                generated_date=datetime.now().strftime('%b %d, %Y'),
                media_colors={
                    'kindle': {'text_color': '#0066CC'},
                    'hardcover': {'text_color': '#6B4BA3'},
                    'audio': {'text_color': '#FF6600'}
                },
                reread_book_ids=reread_book_ids
            )

            # Write the report
            output_path.write_text(html)
            console.print(f"\n[green]Report generated: {output_path}[/green]")

    except Exception as e:
        console.print(f"\n[red]Error generating report: {str(e)}[/red]")
        raise

def main():
    """Main entry point"""
    try:
        generate_chain_report()
    except Exception as e:
        console.print(f"\n[red]Error generating report: {str(e)}[/red]")
        raise

if __name__ == "__main__":
    main()
