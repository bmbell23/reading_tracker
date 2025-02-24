import sys
from pathlib import Path
from sqlalchemy.orm import Session
from rich.console import Console

# Add project root to Python path
from scripts.utils.paths import find_project_root
project_root = find_project_root()
sys.path.insert(0, str(project_root))

from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book

console = Console()

def check_reading(reading_id: int):
    """Check details of a specific reading"""
    session = SessionLocal()
    try:
        reading = session.get(Reading, reading_id)
        if not reading:
            console.print(f"[red]Reading {reading_id} not found[/red]")
            return

        console.print(f"\n[bold]Reading Details for ID {reading_id}:[/bold]")
        console.print(f"Book Title: {reading.book.title}")
        console.print(f"Previous Reading ID: {reading.id_previous}")

        # Check if any reading points to this one
        pointing_to_this = session.query(Reading).filter(Reading.id_previous == reading_id).first()
        if pointing_to_this:
            console.print(f"Next Reading ID: {pointing_to_this.id} ({pointing_to_this.book.title})")
        else:
            console.print("No reading points to this one")

    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print("[red]Usage: python check_reading.py <reading_id>[/red]")
        sys.exit(1)

    reading_id = int(sys.argv[1])
    check_reading(reading_id)