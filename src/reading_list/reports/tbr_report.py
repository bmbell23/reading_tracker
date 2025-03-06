from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine
from typing import Dict, Any
from ..utils.paths import get_project_paths
from ..models.base import SessionLocal
from .chain_report import (
    get_current_readings,
    get_reading_chain,
    organize_chains_by_media
)
from rich.console import Console

console = Console()

def get_cover_path(book_id: int) -> str:
    """Get the path to a book's cover image."""
    if not book_id:
        return "/assets/covers/0.jpg"
    return f"/assets/covers/{book_id}.jpg"

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

    # Combine author names directly
    author = f"{reading.author_name_first or ''} {reading.author_name_second or ''}".strip() or "Unknown Author"

    return {
        'title': reading.title,
        'author': author,
        'date_started': date_started,
        'date_est_start': date_est_start,
        'is_current': is_current,
        'is_future': is_future,
        'cover_url': get_cover_path(reading.book_id),  # Use the new function name
        'read_id': reading.read_id,
        'book_id': reading.book_id
    }

def get_reading_chains_data():
    """Get current reading chains with actual book data"""
    try:
        # Create database session
        db = SessionLocal()
        
        # Get current readings for each media type
        current_readings = get_current_readings(db)
        
        # Initialize chains structure
        chains = {
            'kindle': {'books': [], 'total_books': 0, 'total_pages': 0},
            'hardcover': {'books': [], 'total_books': 0, 'total_pages': 0},
            'audio': {'books': [], 'total_books': 0, 'total_pages': 0}
        }
        
        # For each current reading, get its chain
        for reading in current_readings:
            media = reading.media.lower()
            if media not in chains:
                continue
                
            # Get the chain for this reading
            chain_books = get_reading_chain(db, reading.read_id)
            
            # Process each book in the chain
            for i, book in enumerate(chain_books):
                book_data = get_book_data(
                    book,
                    is_current=(i == 0),
                    is_future=(i > 0)
                )
                chains[media]['books'].append(book_data)
            
            # Update chain statistics
            chains[media]['total_books'] = len(chains[media]['books'])
            # You might want to add total pages calculation here if you have that data
        
        db.close()
        return chains
        
    except Exception as e:
        console.print(f"[red]Error getting reading chains: {str(e)}[/red]")
        if 'db' in locals():
            db.close()
        raise

def generate_tbr_report():
    """Generate TBR report using actual reading chain data."""
    try:
        paths = get_project_paths()
        reports_dir = paths['workspace'] / 'reports' / 'tbr'
        template_dir = paths['templates']
        
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        env.globals['get_cover_path'] = get_cover_path
        
        template = env.get_template('tbr/tbr_manager.html')
        
        # Get actual reading chains data
        chains = get_reading_chains_data()
        
        # Media colors (matching your chain report)
        media_colors = {
            'kindle': {'text_color': '#37A0E8', 'color': '#37A0E8'},
            'hardcover': {'text_color': '#6B4BA3', 'color': '#6B4BA3'},
            'audio': {'text_color': '#F6911E', 'color': '#F6911E'}
        }
        
        # Calculate total books across all chains
        total_books = sum(chain['total_books'] for chain in chains.values())
        
        template_vars = {
            # Changed from string to None since there's no CSRF token in this context
            'csrf_token': None,  
            'title': "TBR Manager",
            'description': "Track your reading progress across different media types",
            'chains': chains,
            'media_colors': media_colors,
            'reading_streak': 0,
            'monthly_progress': 0,
            'reading_pace': 0,
            'pace_trend_icon': "↑",
            'kindle_count': len(chains['kindle']['books']),
            'hardcover_count': len(chains['hardcover']['books']),
            'audio_count': len(chains['audio']['books']),
            'total_books': total_books,
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        output = template.render(**template_vars)
        
        output_file = reports_dir / 'tbr.html'
        output_file.write_text(output)
        
        console.print(f"[green]TBR report generated successfully at: {output_file}[/green]")
        return str(output_file)
        
    except Exception as e:
        console.print(f"[red]Error generating TBR report: {str(e)}[/red]")
        import traceback
        print("\nDebug: Full traceback:")
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    generate_tbr_report()
