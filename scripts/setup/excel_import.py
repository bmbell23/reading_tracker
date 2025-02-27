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
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.reading_list.models.base import SessionLocal
from src.reading_list.models.book import Book
from src.reading_list.models.reading import Reading
from src.reading_list.models.inventory import Inventory

console = Console()

def format_value(value: Any) -> str:
    """Format a value for display"""
    if value is None:
        return "[dim italic]None[/dim italic]"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, bool):
        return "✓" if value else "✗"
    return str(value)

def create_change_table(existing: Any, new_data: Dict[str, Any], title: str) -> Optional[Table]:
    """Create a detailed table showing differences between existing and new data"""
    changes = []
    
    for field, new_value in new_data.items():
        old_value = getattr(existing, field) if existing else None
        # Only consider it a change if the values are actually different
        if old_value != new_value and not (old_value is None and new_value is None):
            changes.append((field, old_value, new_value))
    
    # If no real changes, return None
    if not changes:
        return None
        
    table = Table(
        title=title,
        title_style="bold cyan",
        border_style="bright_black",
        pad_edge=False,
        collapse_padding=True,
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Field", style="bold white")
    table.add_column("Current Value", style="yellow")
    table.add_column("→", style="bright_black", justify="center")
    table.add_column("New Value", style="green")
    
    for field, old_value, new_value in changes:
        table.add_row(
            field,
            format_value(old_value),
            "→",
            format_value(new_value)
        )
    
    return table

def create_summary_panel(changes: List[Tuple[Any, Dict[str, Any]]], new_items: List[Dict[str, Any]], entity_type: str) -> Panel:
    """Create a summary panel of all changes"""
    summary_text = []
    
    if changes:
        summary_text.append(Text(f"\n📝 Updates ({len(changes)} {entity_type}s):", style="bold yellow"))
        for existing, _ in changes:
            title = getattr(existing, 'title', str(existing.id))
            summary_text.append(Text(f"  • {title}", style="yellow"))
    
    if new_items:
        if summary_text:
            summary_text.append(Text(""))  # Add spacing
        summary_text.append(Text(f"\n✨ New ({len(new_items)} {entity_type}s):", style="bold green"))
        for item in new_items:
            summary_text.append(Text(f"  • {item['title']}", style="green"))
    
    if not changes and not new_items:
        summary_text.append(Text(f"\n✓ No changes needed for {entity_type}s", style="dim"))
    
    return Panel(
        Text.assemble(*summary_text),
        title=f"[bold]{entity_type.title()} Changes Summary",
        border_style="bright_black",
        padding=(1, 2)
    )

# Set up logging
logging.basicConfig(
    filename='import_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if pd.isna(date_str):
        return None
    try:
        # First try pandas to_datetime with extended date range
        return pd.to_datetime(date_str, errors='raise', yearfirst=True).to_pydatetime()
    except:
        try:
            # For very old dates, try manual parsing
            if isinstance(date_str, str) and date_str.count('-') == 2:
                year, month, day = map(int, date_str.split('-'))
                return datetime(year, month, day)
            elif isinstance(date_str, str) and len(date_str) == 4:  # Just year
                return datetime(int(date_str), 1, 1)
            else:
                logging.warning(f"Could not parse date: {date_str}")
                return None
        except:
            logging.warning(f"Could not parse date: {date_str}")
            return None

def import_books(session, books_df: pd.DataFrame) -> dict:
    """Import books with progress tracking and conflict resolution"""
    book_id_mapping = {}
    proposed_changes = []
    new_books = []
    
    console.print("\n📚 Analyzing books...")
    
    for _, row in books_df.iterrows():
        try:
            author_parts = str(row['author']).split(' ', 1) if not pd.isna(row['author']) else ['', '']
            author_first = author_parts[0]
            author_second = author_parts[1] if len(author_parts) > 1 else None
            
            # Convert datetime to date for date_published
            date_published = parse_date(row['date_published'])
            if date_published:
                date_published = date_published.date()  # Convert to date object
            
            new_data = {
                'title': row['title'],
                'author_name_first': author_first,
                'author_name_second': author_second,
                'word_count': row['word_count'] if not pd.isna(row['word_count']) else None,
                'page_count': row['page_count'] if not pd.isna(row['page_count']) else None,
                'date_published': date_published,
                'author_gender': row['author_gender'] if not pd.isna(row['author_gender']) else None,
                'series': row['series'] if not pd.isna(row['series']) else None,
                'series_number': row['series_number'] if not pd.isna(row['series_number']) else None,
                'genre': row['genre'] if not pd.isna(row['genre']) else None
            }
            
            existing_book = session.query(Book).filter_by(id=row['id_book']).first()
            if existing_book:
                # Check for actual differences
                changes = {}
                for field, new_value in new_data.items():
                    old_value = getattr(existing_book, field)
                    if isinstance(old_value, datetime):
                        old_value = old_value.date()
                    if old_value != new_value and not (old_value is None and new_value is None):
                        changes[field] = new_value
                
                if changes:  # Only add if there are actual changes
                    proposed_changes.append((existing_book, changes))
            else:
                new_data['id'] = row['id_book']
                new_books.append(new_data)
            
            book_id_mapping[row['id_book']] = row['id_book']
            
        except Exception as e:
            console.print(f"Error processing book: {row.get('title', 'Unknown')}\n{str(e)}", style="red")
    
    # Only proceed if there are actual changes or new books
    if proposed_changes or new_books:
        console.print(f"\nFound {len(proposed_changes)} books to update and {len(new_books)} new books to add.")
        
        if proposed_changes:
            console.print("\n[bold cyan]Changes to be applied:[/bold cyan]")
            for existing, changes in proposed_changes:
                console.print(f"\n[bold]{existing.title}[/bold]")
                for field, new_value in changes.items():
                    old_value = getattr(existing, field)
                    console.print(f"  {field}: {old_value} → {new_value}")
        
        if Confirm.ask("\nDo you want to apply these changes?", default=False):
            for existing, changes in proposed_changes:
                for field, value in changes.items():
                    setattr(existing, field, value)
            
            for book_data in new_books:
                new_book = Book(**book_data)
                session.add(new_book)
            
            session.commit()
            console.print("\n[bold green]✓ Changes applied successfully![/bold green]")
        else:
            console.print("\n[yellow]Import cancelled by user[/yellow]")
            session.rollback()
    else:
        console.print("\n[dim]✓ No changes needed - all books are up to date[/dim]")
    
    return book_id_mapping

def import_excel_data(file_path: str):
    """Main import function with progress tracking and error handling"""
    try:
        with console.status("[bold blue]Reading Excel file...") as status:
            books_df = pd.read_excel(file_path, sheet_name='Books')
            readings_df = pd.read_excel(file_path, sheet_name='Readings')
            inventory_df = pd.read_excel(file_path, sheet_name='Inventory')
        
        session = SessionLocal()
        
        try:
            book_id_mapping = import_books(session, books_df)  # Removed progress parameter
            # TODO: Add similar handling for readings and inventory
            
        except Exception as e:
            session.rollback()
            console.print(Panel(
                str(e),
                title="[red]Import Error",
                border_style="red"
            ))
            raise
        finally:
            session.close()
            
    except Exception as e:
        console.print(Panel(
            f"Failed to read Excel file:\n{str(e)}",
            title="[red]File Error",
            border_style="red"
        ))
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print(Panel(
            "Usage: python excel_import.py <excel_file>",
            title="[yellow]Invalid Usage",
            border_style="yellow"
        ))
        sys.exit(1)
    
    import_excel_data(sys.argv[1])
