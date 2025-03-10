"""Excel import functionality for reading list data."""

import pandas as pd
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import logging
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.panel import Panel
from rich.layout import Layout
from rich.style import Style
from rich.text import Text

from ..models.base import SessionLocal
from ..models.book import Book
from ..models.reading import Reading
from ..models.inventory import Inventory

BOOK_FIELDS = [
    'title',
    'author_name_first',
    'author_name_second',
    'author_gender',
    'word_count',
    'page_count',
    'date_published',
    'series',
    'series_number',
    'genre',
    'cover',
    'isbn_id',
    'isbn_10',
    'isbn_13',
    'asin'
]

console = Console()

def format_value(value: Any) -> str:
    """Format a value for display"""
    if value is None:
        return 'NULL'
    return str(value)

def parse_date(date_str: Any) -> Optional[datetime]:
    """Parse a date string into a datetime object"""
    if pd.isna(date_str):
        return None
    try:
        return pd.to_datetime(date_str, errors='raise', yearfirst=True).to_pydatetime()
    except:
        try:
            if isinstance(date_str, str) and date_str.count('-') == 2:
                year, month, day = map(int, date_str.split('-'))
                return datetime(year, month, day)
            elif isinstance(date_str, str) and len(date_str) == 4:
                return datetime(int(date_str), 1, 1)
            else:
                logging.warning(f"Could not parse date: {date_str}")
                return None
        except:
            logging.warning(f"Could not parse date: {date_str}")
            return None

def import_books(session, books_df: pd.DataFrame, skip_confirmation: bool = False) -> Dict[int, int]:
    """Import books with progress tracking and conflict resolution"""
    proposed_changes = []
    new_books = []
    book_id_mapping = {}
    field_changes = {}  # Track changes by field

    console.print("\n📚 Analyzing books...")

    for _, row in books_df.iterrows():
        try:
            new_data = {field: row[field] for field in BOOK_FIELDS if field in row and not pd.isna(row[field])}
            existing_book = session.query(Book).filter_by(id=row['id_book']).first()
            
            if existing_book:
                changes = {}
                for field, new_value in new_data.items():
                    old_value = getattr(existing_book, field)
                    
                    # Handle date comparison
                    if isinstance(old_value, datetime):
                        old_value = old_value.date()
                    if isinstance(new_value, datetime):
                        new_value = new_value.date()
                    
                    # Only add to changes if values are actually different
                    if old_value != new_value and not (
                        old_value is None and new_value is None or
                        str(old_value) == str(new_value)  # Additional string comparison for dates
                    ):
                        changes[field] = new_value
                        field_changes[field] = field_changes.get(field, 0) + 1

                if changes:  # Only add if there are actual changes
                    proposed_changes.append((existing_book, changes))
            else:
                new_data['id'] = row['id_book']
                new_books.append(new_data)

            book_id_mapping[row['id_book']] = row['id_book']
            
        except Exception as e:
            error_type = str(e)
            if error_type not in errors:
                errors[error_type] = []
            errors[error_type].append(row.get('title', 'Unknown'))

    # Show summary panel
    summary = f"""
[bold cyan]Books Summary[/bold cyan]
• Updates needed: {len(proposed_changes)}
• New books: {len(new_books)}

[bold]Changes by field:[/bold]"""

    for field, count in field_changes.items():
        summary += f"\n• {field}: {count} books"

    if len(proposed_changes) > 0:
        summary += "\n\n[bold]Sample of changes:[/bold]"
        # Show first 3 books as examples
        for existing, changes in proposed_changes[:3]:
            summary += f"\n\n[italic]{existing.title}[/italic]"
            for field, new_value in changes.items():
                old_value = getattr(existing, field)
                summary += f"\n  {field}: {old_value} → {new_value}"
        
        if len(proposed_changes) > 3:
            summary += f"\n\n... and {len(proposed_changes) - 3} more books"

    console.print(Panel(summary.strip(), border_style="blue"))

    if proposed_changes or new_books:
        if not skip_confirmation and Confirm.ask("\nApply these book changes?", default=False):
            for existing, changes in proposed_changes:
                for field, value in changes.items():
                    setattr(existing, field, value)

            for book_data in new_books:
                new_book = Book(**book_data)
                session.add(new_book)

            session.commit()
            console.print("[green]✓ Book changes applied[/green]")
        else:
            console.print("[yellow]Book import cancelled[/yellow]")
            session.rollback()
    else:
        console.print("[dim]✓ No book changes needed[/dim]")

    return book_id_mapping

def import_readings(session, readings_df: pd.DataFrame, book_id_mapping: Dict[int, int], skip_confirmation: bool = False) -> None:
    """Import readings with progress tracking and conflict resolution"""
    proposed_changes = []
    new_readings = []
    skipped_ids = []
    errors = {}

    console.print("\n📖 Analyzing reading sessions...")

    for _, row in readings_df.iterrows():
        try:
            if row['id_book'] not in book_id_mapping:
                skipped_ids.append(row['id_book'])
                continue

            # Parse dates from strings
            date_started = pd.to_datetime(row.get('date_started')).date() if pd.notna(row.get('date_started')) else None
            # Use 'date_finished_actual' from Excel, not 'date_finished'
            date_finished = pd.to_datetime(row.get('date_finished_actual')).date() if pd.notna(row.get('date_finished_actual')) else None

            # Map Excel columns to database fields
            new_data = {
                'book_id': book_id_mapping[row['id_book']],
                'date_started': date_started,
                'date_finished_actual': date_finished,
                'media': row.get('media') if not pd.isna(row.get('media')) else None
            }

            existing_reading = session.query(Reading).filter_by(id=row['id_read']).first()
            if existing_reading:
                changes = {}
                for field, new_value in new_data.items():
                    old_value = getattr(existing_reading, field)
                    if old_value != new_value and new_value is not None:  # Only update if new value is not None
                        changes[field] = new_value

                if changes:
                    proposed_changes.append((existing_reading, changes))
            else:
                new_data['id'] = row['id_read']
                new_readings.append(new_data)

        except Exception as e:
            error_type = str(e)
            if error_type not in errors:
                errors[error_type] = []
            errors[error_type].append(row.get('id_read', 'Unknown'))

    # Show summary panel
    summary = f"""
[bold cyan]Readings Summary[/bold cyan]
• Updates needed: {len(proposed_changes)}
• New readings: {len(new_readings)}

[bold]Proposed Changes:[/bold]"""

    # Show sample of changes
    for reading, changes in proposed_changes[:5]:
        summary += f"\n\nReading ID: {reading.id} (Book: {reading.book.title})"
        for field, new_value in changes.items():
            old_value = getattr(reading, field)
            summary += f"\n  • {field}: {old_value} → {new_value}"
    
    if len(proposed_changes) > 5:
        summary += f"\n\n... and {len(proposed_changes) - 5} more readings"

    if errors:
        summary += "\n\n[bold red]Errors encountered:[/bold red]"
        for error_type, affected_items in errors.items():
            summary += f"\n\n{error_type}:"
            summary += f"\n• Affected {len(affected_items)} items"
            summary += f"\n  - ID: {affected_items[0]}"
            if len(affected_items) > 1:
                summary += f"\n  - ID: {affected_items[1]}"
            if len(affected_items) > 2:
                summary += f"\n  - ... and {len(affected_items) - 2} more"

    console.print(Panel(summary.strip(), border_style="blue"))

    if proposed_changes or new_readings:
        if not skip_confirmation and Confirm.ask("\nApply these reading changes?", default=False):
            for existing, changes in proposed_changes:
                for field, value in changes.items():
                    setattr(existing, field, value)

            for reading_data in new_readings:
                new_reading = Reading(**reading_data)
                session.add(new_reading)

            session.commit()
            console.print("[green]✓ Reading changes applied[/green]")
        else:
            console.print("[yellow]Reading import cancelled[/yellow]")
            session.rollback()
    else:
        console.print("[dim]✓ No reading changes needed[/dim]")

def import_inventory(session, inventory_df: pd.DataFrame, book_id_mapping: Dict[int, int], skip_confirmation: bool = False) -> None:
    """Import inventory with progress tracking and conflict resolution"""
    proposed_changes = []
    new_inventory = []
    skipped_ids = []
    errors = {}

    console.print("\n📚 Analyzing inventory...")

    try:
        for _, row in inventory_df.iterrows():
            try:
                if row['id_book'] not in book_id_mapping:
                    skipped_ids.append(row['id_book'])
                    continue

                new_data = {
                    'book_id': book_id_mapping[row['id_book']],
                    'owned_physical': bool(row['owned_physical']) if not pd.isna(row['owned_physical']) else False,
                    'owned_kindle': bool(row['owned_kindle']) if not pd.isna(row['owned_kindle']) else False,
                    'owned_audio': bool(row['owned_audio']) if not pd.isna(row['owned_audio']) else False
                }

                existing_inventory = session.query(Inventory).filter_by(id=row['id_inventory']).first()
                if existing_inventory:
                    changes = {}
                    for field, new_value in new_data.items():
                        old_value = getattr(existing_inventory, field)
                        if old_value != new_value:
                            changes[field] = new_value

                    if changes:
                        proposed_changes.append((existing_inventory, changes))
                else:
                    new_data['id'] = row['id_inventory']
                    new_inventory.append(new_data)

            except Exception as e:
                error_type = str(e)
                if error_type not in errors:
                    errors[error_type] = []
                errors[error_type].append(row.get('id_inventory', 'Unknown'))

        # Show summary panel
        summary = f"""
[bold cyan]Inventory Summary[/bold cyan]
• Updates needed: {len(proposed_changes)}
• New inventory items: {len(new_inventory)}

[bold]Proposed Changes:[/bold]"""

        # Show sample of changes
        for inv, changes in proposed_changes[:5]:
            summary += f"\n\nInventory ID: {inv.id} (Book: {inv.book.title})"
            for field, new_value in changes.items():
                old_value = getattr(inv, field)
                summary += f"\n  • {field}: {old_value} → {new_value}"
        
        if len(proposed_changes) > 5:
            summary += f"\n\n... and {len(proposed_changes) - 5} more inventory items"

        if errors:
            summary += "\n\n[bold red]Errors encountered:[/bold red]"
            for error_type, affected_items in errors.items():
                summary += f"\n\n{error_type}:"
                summary += f"\n• Affected {len(affected_items)} items"
                summary += f"\n  - ID: {affected_items[0]}"
                if len(affected_items) > 1:
                    summary += f"\n  - ID: {affected_items[1]}"
                if len(affected_items) > 2:
                    summary += f"\n  - ... and {len(affected_items) - 2} more"

        console.print(Panel(summary.strip(), border_style="blue"))

        if proposed_changes or new_inventory:
            if not skip_confirmation and Confirm.ask("\nApply these inventory changes?", default=False):
                for existing, changes in proposed_changes:
                    for field, value in changes.items():
                        setattr(existing, field, value)

                for inventory_data in new_inventory:
                    new_inv = Inventory(**inventory_data)
                    session.add(new_inv)

                session.commit()
                console.print("[green]✓ Inventory changes applied[/green]")
            else:
                console.print("[yellow]Inventory import cancelled[/yellow]")
                session.rollback()
        else:
            console.print("[dim]✓ No inventory changes needed[/dim]")

    except Exception as e:
        console.print(f"[red]Error processing inventory: {str(e)}[/red]")
        session.rollback()
        raise

def import_excel_data(filepath: str, skip_confirmation: bool = False):
    """Import data from Excel file into the database."""
    try:
        with console.status("[bold blue]Reading Excel file...") as status:
            books_df = pd.read_excel(filepath, sheet_name='Books')
            readings_df = pd.read_excel(filepath, sheet_name='Readings')
            inventory_df = pd.read_excel(filepath, sheet_name='Inventory')

        session = SessionLocal()
        try:
            # Import each table separately with its own confirmation
            book_id_mapping = import_books(session, books_df, skip_confirmation)
            import_readings(session, readings_df, book_id_mapping, skip_confirmation)
            import_inventory(session, inventory_df, book_id_mapping, skip_confirmation)

            console.print("\n[bold green]✓ Import completed successfully![/bold green]")

        except Exception as e:
            session.rollback()
            console.print(Panel(str(e), title="[red]Import Error", border_style="red"))
            raise
        finally:
            session.close()

    except Exception as e:
        console.print(Panel(f"Failed to read Excel file:\n{str(e)}", title="[red]File Error", border_style="red"))
        raise
