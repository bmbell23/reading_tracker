"""Command to sync cover status in database with actual cover files."""
import argparse
from pathlib import Path
from rich.console import Console
from sqlalchemy import text

from ..utils.paths import get_project_paths
from ..models.base import engine

console = Console()

def add_subparser(subparsers):
    """Add the sync-covers command parser to the main parser."""
    parser = subparsers.add_parser(
        "sync-covers",
        help="Sync cover status in database with actual cover files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    return parser

def handle_command(args):
    """Handle the sync-covers command."""
    try:
        covers_path = get_project_paths()['assets'] / 'book_covers'
        
        # Get all cover file IDs
        cover_ids = set()
        for file in covers_path.iterdir():
            if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    book_id = int(file.stem.split('_')[1])
                    cover_ids.add(book_id)
                except (IndexError, ValueError):
                    continue

        # Update database
        with engine.connect() as conn:
            # Reset all cover statuses to False
            conn.execute(text("UPDATE books SET cover = 0"))
            
            # Set cover = True for books that have cover files
            if cover_ids:
                id_list = ','.join(str(id) for id in cover_ids)
                conn.execute(text(f"UPDATE books SET cover = 1 WHERE id IN ({id_list})"))
            
            conn.commit()

        console.print("[green]Cover status sync completed successfully![/green]")
        return 0
        
    except Exception as e:
        console.print(f"[red]Error syncing covers: {str(e)}[/red]")
        return 1
