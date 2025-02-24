import sys
from pathlib import Path
from sqlalchemy.orm import Session
from rich.console import Console
from rich.table import Table

# Add project root to Python path
from scripts.utils.paths import find_project_root
project_root = find_project_root()
sys.path.insert(0, str(project_root))

from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book

console = Console()

def fix_hardcover_chain(session: Session):
    """Fix the hardcover reading chain to the correct order"""
    # Define the correct chain order by reading IDs
    chain_order = [414, 405, 406, 733, 424, 395]

    console.print("\n[bold]Fixing hardcover reading chain...[/bold]")

    # Create a table to show the changes
    table = Table(title="Chain Updates")
    table.add_column("Position", style="cyan")
    table.add_column("Reading ID", style="green")
    table.add_column("Previous ID", style="yellow")
    table.add_column("Book Title", style="blue")

    try:
        # Update the chain links
        for i, reading_id in enumerate(chain_order):
            reading = session.get(Reading, reading_id)
            if not reading:
                console.print(f"[red]Error: Reading {reading_id} not found[/red]")
                continue

            # Set the previous ID (None for first reading)
            prev_id = chain_order[i-1] if i > 0 else None
            reading.id_previous = prev_id

            # Add to display table
            table.add_row(
                str(i+1),
                str(reading_id),
                str(prev_id) if prev_id else "None",
                reading.book.title
            )

        # Show the proposed changes
        console.print(table)

        # Confirm before committing
        if console.input("\n[yellow]Commit these changes? (y/N): [/yellow]").lower() == 'y':
            session.commit()
            console.print("[green]Chain fixed successfully![/green]")
        else:
            session.rollback()
            console.print("[yellow]Changes cancelled[/yellow]")

    except Exception as e:
        session.rollback()
        console.print(f"[red]Error: {str(e)}[/red]")

def main():
    session = SessionLocal()
    try:
        fix_hardcover_chain(session)
    finally:
        session.close()

if __name__ == "__main__":
    main()
