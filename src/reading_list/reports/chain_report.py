"""
Reading Chain Report Generator
============================

Generates reports showing the current state of reading chains.
"""

from typing import List, Dict, Any
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

console = Console()

def get_current_readings(conn) -> List[Dict[str, Any]]:
    """Get all current readings"""
    query = """
        SELECT
            r.id as read_id,
            r.media,
            r.date_started,
            r.date_finished_actual,
            b.id as book_id,
            b.title
        FROM read r
        JOIN books b ON r.book_id = b.id
        WHERE r.date_started IS NOT NULL
        AND r.date_finished_actual IS NULL
        ORDER BY r.media;
    """
    results = conn.execute(text(query)).fetchall()

    # Debug output
    console.print("\n[bold]Current Readings Found:[/bold]")
    for r in results:
        console.print(f"ID: {r.read_id}, Title: {r.title}, Media: {r.media}")
        console.print(f"Started: {r.date_started}, Finished: {r.date_finished_actual}")

    return results

def get_reading_chain(conn, reading_id: int) -> List[Dict[str, Any]]:
    """
    Get the reading chain from current reading forward
    
    Args:
        conn: Database connection
        reading_id: ID of the reading to get chain for
    """
    query = """
        WITH RECURSIVE forward AS (
            -- Initial (current) reading
            SELECT
                r.id as read_id,
                r.id_previous,
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
                b.page_count,
                0 as position
            FROM read r
            JOIN books b ON r.book_id = b.id
            WHERE r.id = :reading_id

            UNION ALL

            -- Next books in chain
            SELECT
                r.id as read_id,
                r.id_previous,
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
                b.page_count,
                fw.position + 1
            FROM read r
            JOIN books b ON r.book_id = b.id
            JOIN forward fw ON r.id_previous = fw.read_id
        )
        SELECT * FROM forward
        ORDER BY position;
    """
    
    results = conn.execute(text(query), {"reading_id": reading_id}).fetchall()
    return results

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

def get_book_data(reading: Dict[str, Any], is_current: bool = False, is_future: bool = False) -> Dict[str, Any]:
    """Get formatted book data including cover URL"""
    
    # Convert string dates to datetime if they're strings
    date_started = None
    if reading.date_started:
        date_started = (
            reading.date_started 
            if isinstance(reading.date_started, datetime) 
            else datetime.strptime(reading.date_started, '%Y-%m-%d')
        )

    date_est_start = None
    if reading.date_est_start:
        date_est_start = (
            reading.date_est_start 
            if isinstance(reading.date_est_start, datetime) 
            else datetime.strptime(reading.date_est_start, '%Y-%m-%d')
        )

    return {
        'title': reading.title,
        'author': format_author_name(reading.author_name_first, reading.author_name_second),
        'date_started': date_started,
        'date_est_start': date_est_start,
        'date_est_end': reading.date_est_end,
        'word_count': reading.word_count,
        'page_count': reading.page_count,
        'is_current': is_current,
        'is_future': is_future,
        'cover_url': get_book_cover_path(reading.book_id),
        'read_id': reading.read_id,
        'book_id': reading.book_id
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

def generate_chain_report() -> None:
    """Generate the reading chain report"""
    try:
        project_paths = get_project_paths()
        reports_dir = project_paths['workspace'] / 'reports' / 'tbr'
        output_path = reports_dir / 'to_be_read.html'
        reports_dir.mkdir(parents=True, exist_ok=True)
        ensure_directory(reports_dir)

        with SessionLocal() as session:
            # Get current readings
            current_readings = get_current_readings(session)
            
            # Get chains for each current reading and combine them
            all_books = []
            for reading in current_readings:
                chain = get_reading_chain(session, reading.read_id)
                if chain:
                    # Format each book in the chain
                    for idx, book in enumerate(chain):
                        formatted_book = {
                            'title': book.title,
                            'author': format_author_name(book.author_name_first, book.author_name_second),
                            'date_started': format_date(book.date_started),
                            'date_est_start': format_date(book.date_est_start),
                            'date_est_end': format_date(book.date_est_end),
                            'word_count': book.word_count,
                            'page_count': book.page_count,
                            'is_current': idx == 0,
                            'is_future': idx > 0,
                            'cover_url': get_book_cover_path(book.book_id),
                            'read_id': book.read_id,
                            'book_id': book.book_id,
                            'media': reading.media
                        }
                        all_books.append(formatted_book)

            # Sort books: current books first, then by estimated start date and title
            sorted_books = sorted(all_books, key=lambda x: (
                not x['is_current'],  # False sorts before True, so current books come first
                x['date_est_start'] or '9999-12-31',  # Books without est_start date go last
                x['title'].lower()  # Use title as tie-breaker
            ))

            # Set up Jinja2 environment
            template_dir = project_paths['templates'] / 'reports' / 'chain'
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('reading_chain_report.html')

            # Generate HTML
            html = template.render(
                books=sorted_books,
                media_colors={
                    'kindle': {'text_color': '#0066CC'},     # Deeper Kindle blue
                    'hardcover': {'text_color': '#6B4BA3'},  # Space purple
                    'audio': {'text_color': '#FF6600'}       # Warmer Audible orange
                }
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
