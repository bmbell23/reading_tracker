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
from ..utils.paths import get_project_paths, find_project_root

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
                fw.position + 1
            FROM read r
            JOIN books b ON r.book_id = b.id
            JOIN forward fw ON r.id_previous = fw.read_id
            WHERE fw.position < 10  -- Limit to 10 future books
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
        cover_path = f"assets/book_covers/{book_id}{ext}"
        if (covers_path / f"{book_id}{ext}").exists():
            return cover_path

    return "assets/book_covers/0.jpg"

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
        'is_current': is_current,
        'is_future': is_future,
        'cover_url': get_book_cover_path(reading.book_id),
        'read_id': reading.read_id,
        'book_id': reading.book_id
    }

def generate_chain_report() -> None:
    """Generate the reading chain report"""
    project_paths = get_project_paths()
    
    # Set up Jinja environment with correct template directory
    template_dir = project_paths['workspace'] / 'src' / 'reading_list' / 'templates'
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    # Media type colors - updated to match standardized colors
    media_colors = {
        'kindle': {'text_color': '#3B82F6'},    # blue
        'hardcover': {'text_color': '#A855F7'},  # purple
        'audio': {'text_color': '#FB923C'}       # warm orange
    }

    try:
        session = SessionLocal()
        # Get current readings
        current_readings = get_current_readings(session)
        
        # Organize chains by media type
        chains = {}
        for reading in current_readings:
            media = reading.media.lower()
            if media not in chains:
                chains[media] = {'chain': []}
            
            chain = get_reading_chain(session, reading.read_id)
            chains[media]['chain'] = [
                get_book_data(book, book.read_id == reading.read_id, not book.date_started)
                for book in chain
            ]

        # Get template and render
        template = env.get_template('reports/chain/reading_chain.html')
        html = template.render(
            title="Reading Chains",
            description="Current and upcoming books in each reading chain",
            chains=chains,
            media_colors=media_colors,
            generated_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Create output directory if it doesn't exist
        output_path = project_paths['workspace'] / 'reports' / 'reading_chain.html'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        
        console.print(f"\n[green]Report generated: {output_path}[/green]")
    finally:
        session.close()

def main():
    """Main entry point"""
    try:
        generate_chain_report()
    except Exception as e:
        console.print(f"\n[red]Error generating report: {str(e)}[/red]")
        raise

if __name__ == "__main__":
    main()
