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
            ),
            NextReadings AS (
                -- Get the next planned reading for each book using ROW_NUMBER
                SELECT *
                FROM (
                    SELECT 
                        book_id,
                        media,
                        id as read_id,
                        date_started,
                        date_est_start,
                        date_est_end,
                        days_estimate,
                        ROW_NUMBER() OVER (
                            PARTITION BY book_id 
                            ORDER BY COALESCE(date_started, date_est_start) ASC
                        ) as rn
                    FROM read
                    WHERE date_finished_actual IS NULL
                )
                WHERE rn = 1
            )
            SELECT
                nr.read_id,
                b.id as book_id,
                b.title,
                b.author_name_first || ' ' || COALESCE(b.author_name_second, '') as author,
                i.owned_physical,
                i.owned_kindle,
                i.owned_audio,
                nr.media as planned_media,
                nr.date_started,
                nr.date_est_start,
                nr.date_est_end,
                nr.days_estimate,
                b.word_count
            FROM books b
            JOIN inv i ON b.id = i.book_id
            LEFT JOIN NextReadings nr ON b.id = nr.book_id
            LEFT JOIN FinishedReads fr ON b.id = fr.book_id
            WHERE fr.book_id IS NULL
            AND (i.owned_physical = TRUE OR i.owned_kindle = TRUE OR i.owned_audio = TRUE)
            ORDER BY
                COALESCE(nr.date_est_start, nr.date_started) ASC,
                b.title ASC
        """)

        results = session.execute(query).mappings().all()
        organized = {
            'physical': [],
            'kindle': [],
            'audio': [],
            'no_read_entry': []
        }

        for row in results:
            book_data = dict(row)
            
            if not book_data['read_id']:
                book_data['planned_media'] = 'unplanned'
                organized['no_read_entry'].append(book_data)
                continue

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
    table.add_column("Media", style="bold")
    table.add_column("Start Date", style="yellow")  # Combined column
    table.add_column("Est. End", style="yellow")
    table.add_column("Days Est.", justify="right", style="yellow")
    table.add_column("Words", justify="right", style="green")

    return table

def add_books_to_table(table: Table, books: List[Dict]) -> None:
    """Add books to the table."""
    media_colors = {
        'hardcover': '#6B4BA3',  # Space purple
        'kindle': '#0066CC',     # Deeper Kindle blue
        'audio': '#FF6600',      # Warmer Audible orange
        'unplanned': 'white'
    }

    total_books = 0
    total_words = 0

    for book in books:
        word_count = book['word_count'] or 0
        total_books += 1
        total_words += word_count

        # Get the earliest start date (actual or estimated)
        start_date = book.get('date_started') or book.get('date_est_start', '')
        
        media = book.get('planned_media', 'unplanned').lower()
        media_color = media_colors.get(media, 'white')
        media_display = media.title()  # Capitalize first letter

        table.add_row(
            str(book['read_id'] or ''),
            book['title'],
            book['author'],
            f"[{media_color}]{media_display}[/{media_color}]",
            str(start_date),
            str(book.get('date_est_end', '')),
            str(book.get('days_estimate', '')),
            f"{word_count:,}" if word_count else ""
        )

    # Add total row
    table.add_row(
        "",
        f"[bold]Total ({total_books} books)[/bold]",
        "",
        "",
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
        
        # Combine all books into a single list
        all_unread_books = []
        all_unread_books.extend(inventory['physical'])
        all_unread_books.extend(inventory['kindle'])
        all_unread_books.extend(inventory['audio'])

        # Sort by start date and title
        all_unread_books.sort(key=lambda x: (
            x.get('date_started') or x.get('date_est_start') or '',
            x['title']
        ))

        # Create and display single table
        table = create_books_table("Unread Books")
        add_books_to_table(table, all_unread_books)
        console.print(table)

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