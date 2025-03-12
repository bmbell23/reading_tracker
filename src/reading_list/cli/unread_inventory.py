#!/usr/bin/env python3
"""CLI command to display unread books from inventory."""
from typing import List, Dict, Optional
import datetime  # Add this import
from sqlalchemy import text
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from ..models.base import SessionLocal
from ..operations.chain_operations import ChainOperations
from .update_entries import DatabaseUpdater

console = Console()

def get_unread_inventory() -> Dict[str, List[Dict]]:
    """Get all unread books from inventory, organized by format."""
    with SessionLocal() as session:
        query = text("""
            WITH FinishedReads AS (
                SELECT DISTINCT book_id
                FROM read
                WHERE date_finished_actual IS NOT NULL
            )
            SELECT
                r.id as read_id,
                b.id as book_id,
                b.title,
                b.author_name_first || ' ' || COALESCE(b.author_name_second, '') as author,
                i.owned_physical,
                i.owned_kindle,
                i.owned_audio,
                COALESCE(r.date_started, r.date_est_start) as start_date,
                COALESCE(r.date_finished_actual, r.date_est_end) as finish_date,
                b.word_count
            FROM books b
            JOIN inv i ON b.id = i.book_id
            LEFT JOIN read r ON b.id = r.book_id
            LEFT JOIN FinishedReads fr ON b.id = fr.book_id
            WHERE fr.book_id IS NULL
            AND (i.owned_physical = TRUE OR i.owned_kindle = TRUE OR i.owned_audio = TRUE)
            ORDER BY
                COALESCE(r.date_started, r.date_est_start) ASC NULLS LAST,
                b.title ASC
        """)

        results = session.execute(query).mappings().all()

        # Organize by format
        organized = {
            'physical': [],
            'kindle': [],
            'audio': [],
            'no_read_entry': []
        }

        for row in results:
            book_data = dict(row)

            # Check if book has no read entry
            if not book_data['read_id']:
                organized['no_read_entry'].append(book_data)
                continue

            # Add to respective format lists based on ownership
            if book_data['owned_physical']:
                organized['physical'].append(book_data)
            if book_data['owned_kindle']:
                organized['kindle'].append(book_data)
            if book_data['owned_audio']:
                organized['audio'].append(book_data)

        return organized

def create_books_table(title: str) -> Table:
    """Create a table for displaying books."""
    table = Table(
        title=title,
        show_header=True,
        header_style="bold magenta"
    )

    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Author", style="white")
    table.add_column("Start", style="yellow")
    table.add_column("Finish", style="yellow")
    table.add_column("Words", justify="right", style="green")

    return table

def add_books_to_table(table: Table, books: List[Dict]) -> None:
    """Add books to the table."""
    total_books = 0
    total_words = 0

    for book in books:
        word_count = book['word_count'] or 0
        total_books += 1
        total_words += word_count

        # Format dates properly
        start_date = str(book.get('start_date', '')) if book.get('start_date') else ''
        finish_date = str(book.get('finish_date', '')) if book.get('finish_date') else ''

        table.add_row(
            str(book['read_id'] or ''),  # Changed from book_id to read_id
            book['title'],
            book['author'],
            start_date,
            finish_date,
            f"{word_count:,}" if word_count else ""
        )

    # Add total row
    table.add_row(
        "",
        f"[bold]Total ({total_books} books)[/bold]",
        "",
        "",
        "",
        f"[bold green]{total_words:,}[/bold green]",
        style="bold white"
    )

def handle_missing_read_entries(books: List[Dict]):
    """Handle books that don't have any reading entries."""
    if not books:
        return

    # Display books without read entries
    table = create_books_table("Unread Books Without Reading Entries")
    add_books_to_table(table, books)
    console.print(table)

    if Confirm.ask("\nWould you like to add reading entries for these books?"):
        updater = DatabaseUpdater()  # Remove the session parameter
        for book in books:
            if Confirm.ask(f"\nAdd reading entry for '{book['title']}'?"):
                updater._create_new_reading(book['book_id'])

def display_books(books: List[Dict], format_type: str) -> None:
    """Display books of a specific format."""
    if not books:
        return

    # Create title with format type capitalized
    title = f"Unread {format_type.capitalize()} Books"

    # Create and populate table
    table = create_books_table(title)
    add_books_to_table(table, books)

    # Display the table
    console.print(table)

def main():
    """Main entry point for unread inventory command."""
    try:
        inventory = get_unread_inventory()

        # Display books by format
        display_books(inventory['physical'], 'physical')
        display_books(inventory['kindle'], 'kindle')
        display_books(inventory['audio'], 'audio')

        # Handle books without read entries
        handle_missing_read_entries(inventory['no_read_entry'])

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

    return 0

def add_subparser(subparsers):
    """Add the unread-inventory subparser to the main parser."""
    parser = subparsers.add_parser(
        "unread-inventory",
        help="Display unread books from inventory"
    )
    return parser

def handle_command(args):
    """Handle the unread-inventory command."""
    return main()

if __name__ == "__main__":
    main()