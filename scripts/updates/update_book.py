"""
Database Update Utility
======================

A command-line interface for updating book-related database entries across three tables:
- books: Main book information
- read: Reading session records
- inv: Book inventory tracking

The utility provides an interactive interface to:
1. Search for entries by ID or title
2. Display search results in formatted tables
3. Update existing entries with validation
4. Create new related entries in other tables
5. Chain updates across related tables

Key Components:
-------------
- Input Handling: Uses Rich's Prompt and Confirm for user interaction
- Data Validation: Type-specific parsing and validation functions
- Display Formatting: Rich console formatting with tables and panels
- Database Operations: SQLAlchemy session management and queries
- Error Handling: Transaction management with rollback on failure

Main Functions:
-------------
parse_date(date_str: str) -> Optional[date]:
    Parses date strings in YYYY-MM-DD format with validation

parse_boolean(value: str) -> bool:
    Converts string inputs to boolean values

search_entries(session, model, search_term: str, search_by_id: bool) -> List:
    Searches database entries with model-specific logic

display_search_results(entries: List, model, session):
    Displays search results in formatted tables

display_entry_card(entry, model):
    Shows detailed entry information after updates

get_book_input(session, is_new: bool, existing_book) -> Dict:
    Collects and validates book entry updates

get_reading_input(session, book_id, existing_reading) -> Dict:
    Collects and validates reading entry updates

get_inventory_input(session, book_id, existing_inventory) -> Dict:
    Collects and validates inventory entry updates

Usage Flow:
----------
1. Select table to modify (books/read/inv)
2. Search for entries by ID or title
3. Select entry to update from results
4. Input new values with validation
5. Optionally update related entries in other tables
6. Commit changes or rollback on error

Error Handling:
-------------
- Invalid date formats
- Invalid boolean inputs
- Database constraints
- Transaction failures
"""

"""
Database Update Utility
======================

A command-line interface for updating book-related database entries across three tables:
- books: Main book information
- read: Reading session records
- inv: Book inventory tracking

The utility provides an interactive interface to:
1. Search for entries by ID or title
2. Display search results in formatted tables
3. Update existing entries with validation
4. Create new related entries in other tables
5. Chain updates across related tables

Key Components:
-------------
- Input Handling: Uses Rich's Prompt and Confirm for user interaction
- Data Validation: Type-specific parsing and validation functions
- Display Formatting: Rich console formatting with tables and panels
- Database Operations: SQLAlchemy session management and queries
- Error Handling: Transaction management with rollback on failure

Main Functions:
-------------
parse_date(date_str: str) -> Optional[date]:
    Parses date strings in YYYY-MM-DD format with validation

parse_boolean(value: str) -> bool:
    Converts string inputs to boolean values

search_entries(session, model, search_term: str, search_by_id: bool) -> List:
    Searches database entries with model-specific logic

display_search_results(entries: List, model, session):
    Displays search results in formatted tables

display_entry_card(entry, model):
    Shows detailed entry information after updates

get_book_input(session, is_new: bool, existing_book) -> Dict:
    Collects and validates book entry updates

get_reading_input(session, book_id, existing_reading) -> Dict:
    Collects and validates reading entry updates

get_inventory_input(session, book_id, existing_inventory) -> Dict:
    Collects and validates inventory entry updates

Usage Flow:
----------
1. Select table to modify (books/read/inv)
2. Search for entries by ID or title
3. Select entry to update from results
4. Input new values with validation
5. Optionally update related entries in other tables
6. Commit changes or rollback on error

Error Handling:
-------------
- Invalid date formats
- Invalid boolean inputs
- Database constraints
- Transaction failures
"""

import sys
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from scripts.utils.paths import find_project_root
from sqlalchemy import func, or_

from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from src.models.inventory import Inventory

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(project_root))


# Initialize Rich console
console = Console()
error_style = Style(color="red", bold=True)
success_style = Style(color="green", bold=True)
header_style = Style(color="blue", bold=True)

def get_next_id(session, model):
    """Get the next available ID for a given model"""
    max_id = session.query(func.max(model.id)).scalar()
    return 1 if max_id is None else max_id + 1

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        console.print("Invalid date format. Please use YYYY-MM-DD", style=error_style)
        return None

def parse_boolean(value):
    """Parse string to boolean"""
    return value.lower() in ('yes', 'true', 't', 'y', '1')

def search_entries(session, model, search_term, search_by_id=False):
    """Search for entries in a given model"""
    if search_by_id:
        try:
            entry = session.query(model).filter(model.id == int(search_term)).first()
            return [entry] if entry else []
        except ValueError:
            return []

    if model == Book:
        return session.query(model).filter(
            or_(
                Book.title.ilike(f"%{search_term}%"),
                Book.author_name_first.ilike(f"%{search_term}%"),
                Book.author_name_second.ilike(f"%{search_term}%")
            )
        ).all()
    elif model == Reading:
        return session.query(model).join(Book).filter(
            Book.title.ilike(f"%{search_term}%")
        ).all()
    elif model == Inventory:
        return session.query(model).join(Book).filter(
            Book.title.ilike(f"%{search_term}%")
        ).all()

def display_search_results(entries, model, session):
    """Display search results in a table"""
    table = Table(title="Search Results")

    if model == Book:
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Author First", style="green")
        table.add_column("Author Second", style="green")

        for entry in entries:
            table.add_row(
                str(entry.id),
                entry.title,
                entry.author_name_first or '',
                entry.author_name_second or ''
            )
    elif model == Reading:
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Book", style="magenta")
        table.add_column("Started", style="green")
        table.add_column("Finished", style="green")

        for entry in entries:
            book = session.get(Book, entry.book_id)
            table.add_row(
                str(entry.id),
                book.title if book else "Unknown",
                str(entry.date_started) if entry.date_started else '',
                str(entry.date_finished_actual) if entry.date_finished_actual else ''
            )
    else:  # Inventory
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Book", style="magenta")
        table.add_column("Formats", style="green")
        table.add_column("Location", style="green")

        for entry in entries:
            book = session.get(Book, entry.book_id)
            formats = []
            if entry.owned_physical:
                formats.append("Physical")
            if entry.owned_kindle:
                formats.append("Kindle")
            if entry.owned_audio:
                formats.append("Audio")

            table.add_row(
                str(entry.id),
                book.title if book else "Unknown",
                ", ".join(formats),
                entry.location or ''
            )

    console.print(table)

def search_and_select_entry(session, model, console):
    """Search for and select an entry to update"""
    while True:
        search_term = Prompt.ask("Enter ID or title to search")

        # Try to parse as ID first
        try:
            id_entries = search_entries(session, model, search_term, search_by_id=True)
        except ValueError:
            id_entries = []

        # Always search titles too
        title_entries = search_entries(session, model, search_term, search_by_id=False)

        # Combine results, removing duplicates
        entries = list({entry.id: entry for entry in (id_entries + title_entries)}.values())

        if not entries:
            console.print("No matching entries found", style=error_style)
            create_new = Prompt.ask("Would you like to create a new entry? (y/n)", choices=["y", "n"], default="y")

            if create_new.lower() == "y":
                if model == Book:
                    data = get_book_input(session, is_new=True, existing_book=None)
                    if data:
                        new_entry = model(**data)
                        session.add(new_entry)
                        session.commit()
                        console.print("\n[bold green]New entry created successfully![/bold green]")
                        display_entry_card(new_entry, model)
                        return new_entry
                elif model == Reading:
                    console.print("Please create the book entry first before adding a reading record", style="yellow")
                else:  # Inventory
                    console.print("Please create the book entry first before adding an inventory record", style="yellow")

            try_again = Prompt.ask("Try another search? (y/n)", choices=["y", "n"], default="n")
            if try_again.lower() != "y":
                return None
            continue

        display_search_results(entries, model, session)

        if len(entries) == 1:
            response = Prompt.ask("Is this the correct entry? [y/n]", default="y")
            if response.lower() not in ['n', 'no']:  # Enter or any other input except 'n'/'no' means yes
                return entries[0]
        else:
            entry_id = Prompt.ask("Enter the ID of the correct entry (or press Enter to search again)")
            if entry_id:
                selected = next((e for e in entries if str(e.id) == entry_id), None)
                if selected:
                    # If user entered an ID from the displayed results, select it without confirmation
                    entry = selected
                else:
                    response = Prompt.ask("Is this the correct entry? [y/n]", default="y")
                    if response.lower() not in ['n', 'no']:  # Enter or any other input except 'n'/'no' means yes
                        return selected

        if not Confirm.ask("Try another search?", default=False):
            return None

def get_book_input(session, is_new=True, existing_book=None):
    """Get book information from user"""
    data = {}
    if not is_new:
        if existing_book:
            data['id'] = existing_book.id
        else:
            title = Prompt.ask("Enter book title to update")
            existing_book = session.query(Book).filter(Book.title == title).first()
            if not existing_book:
                console.print(f"Book '{title}' not found", style=error_style)
                return None
            data['id'] = existing_book.id
    else:
        data['id'] = get_next_id(session, Book)

    fields = [
        ('title', str, "Title"),
        ('author_name_first', str, "Author first name"),
        ('author_name_second', str, "Author last name"),
        ('word_count', int, "Word count"),
        ('page_count', int, "Page count"),
        ('date_published', parse_date, "Date published (YYYY-MM-DD)"),
        ('author_gender', str, "Author gender"),
        ('series', str, "Series"),
        ('series_number', int, "Series number"),
        ('genre', str, "Genre")
    ]

    console.print(Panel(
        "Book Information",
        style=header_style
    ))

    for field, type_conv, prompt in fields:
        if not is_new:
            current_value = getattr(existing_book, field)
            while True:
                try:
                    value = Prompt.ask(f"{prompt} [cyan](current: {current_value})[/cyan]")
                    if not value:  # User just pressed Enter
                        break
                    data[field] = type_conv(value)
                    break
                except ValueError:
                    console.print(f"Invalid input for {field}. Please try again.", style=error_style)
        else:
            while True:
                try:
                    value = Prompt.ask(f"{prompt}")
                    if not value:
                        data[field] = None
                        break
                    data[field] = type_conv(value)
                    break
                except ValueError:
                    console.print(f"Invalid input for {field}. Please try again.", style=error_style)

    return data

def get_reading_input(session, book_id, existing_reading=None):
    """Get reading information from user"""
    data = {
        'id': existing_reading.id if existing_reading else get_next_id(session, Reading),
        'book_id': book_id
    }

    console.print(Panel(
        "Reading Information",
        style=header_style
    ))

    fields = [
        ('id_previous', int, "Previous reading ID"),
        ('media', str, "Media type [cyan](Hardcover/Kindle/Audio)[/cyan]"),
        ('date_started', parse_date, "Date started [cyan](YYYY-MM-DD)[/cyan]"),
        ('date_finished_actual', parse_date, "Date finished [cyan](YYYY-MM-DD)[/cyan]")
    ]

    for field, type_conv, prompt in fields:
        while True:
            try:
                current_value = getattr(existing_reading, field) if existing_reading else None
                value = Prompt.ask(f"{prompt} [cyan](current: {current_value})[/cyan]")
                if not value:
                    data[field] = None
                    break
                data[field] = type_conv(value)
                break
            except ValueError:
                console.print(f"Invalid input for {field}. Please try again.", style=error_style)

    return data

def get_inventory_input(session, book_id, existing_inventory=None):
    """Get inventory information from user"""
    data = {
        'id': existing_inventory.id if existing_inventory else get_next_id(session, Inventory),
        'book_id': book_id
    }

    console.print(Panel(
        "Inventory Information",
        style=header_style
    ))

    fields = [
        ('owned_audio', parse_boolean, "Owned in audio?"),
        ('owned_kindle', parse_boolean, "Owned in Kindle?"),
        ('owned_physical', parse_boolean, "Owned in physical?"),
        ('date_purchased', parse_date, "Date purchased [cyan](YYYY-MM-DD)[/cyan]"),
        ('location', str, "Location")
    ]

    for field, type_conv, prompt in fields:
        while True:
            try:
                current_value = getattr(existing_inventory, field) if existing_inventory else None
                if field in ['owned_audio', 'owned_kindle', 'owned_physical']:
                    response = Prompt.ask(
                        f"{prompt} [cyan](current: {current_value})[/cyan]",
                        choices=['y', 'n'],
                        default='n'
                    )
                    data[field] = response.lower() == 'y'
                    break
                else:
                    value = Prompt.ask(f"{prompt} [cyan](current: {current_value})[/cyan]")
                    if not value:
                        data[field] = None
                        break
                    data[field] = type_conv(value)
                    break
            except ValueError:
                console.print(f"Invalid input for {field}. Please try again.", style=error_style)

    return data

def display_entry_card(entry, model):
    """Display a detailed card of the entry after update"""
    if model == Book:
        # Format author name properly before displaying
        author = f"{entry.author_name_first or ''} {entry.author_name_second or ''}".strip()

        panel_content = "\n".join([
            "[bold cyan]Book Details[/bold cyan]",
            "",
            f"[bold white]ID:[/bold white] {entry.id}",
            f"[bold white]Title:[/bold white] {entry.title}",
            f"[bold white]Author:[/bold white] {author}",
            f"[bold white]Word Count:[/bold white] {entry.word_count or 'N/A'}",
            f"[bold white]Page Count:[/bold white] {entry.page_count or 'N/A'}",
            f"[bold white]Published:[/bold white] {entry.date_published or 'N/A'}",
            f"[bold white]Author Gender:[/bold white] {entry.author_gender or 'N/A'}"
        ])

        console.print(Panel(panel_content, title="Updated Entry", border_style="green"))

    elif model == Reading:
        panel_content = "\n".join([
            "[bold cyan]Reading Session Details[/bold cyan]",
            "",
            f"[bold white]ID:[/bold white] {entry.id}",
            f"[bold white]Book:[/bold white] {entry.book.title}",
            f"[bold white]Started:[/bold white] {entry.date_started or 'N/A'}",
            f"[bold white]Finished:[/bold white] {entry.date_finished_actual or 'N/A'}",
            f"[bold white]Est. Completion:[/bold white] {entry.date_est_end or 'N/A'}",
            f"[bold white]Media:[/bold white] {entry.media or 'N/A'}",
            f"[bold white]Previous Reading:[/bold white] {entry.id_previous or 'N/A'}"
        ])

        console.print(Panel(panel_content, title="Updated Entry", border_style="green"))

    elif model == Inventory:
        formats = []
        if entry.owned_physical: formats.append("Physical")
        if entry.owned_kindle: formats.append("Kindle")
        if entry.owned_audio: formats.append("Audio")

        panel_content = "\n".join([
            "[bold cyan]Inventory Details[/bold cyan]",
            "",
            f"[bold white]ID:[/bold white] {entry.id}",
            f"[bold white]Book:[/bold white] {entry.book.title}",
            f"[bold white]Formats:[/bold white] {', '.join(formats) if formats else 'None'}",
            f"[bold white]Location:[/bold white] {entry.location or 'N/A'}",
            f"[bold white]Read Count:[/bold white] {entry.read_count or '0'}"
        ])

        console.print(Panel(panel_content, title="Updated Entry", border_style="green"))

def main():
    console.print(Panel(
        "Database Update Utility",
        style=header_style
    ))

    models = {
        "books": Book,
        "read": Reading,
        "inv": Inventory
    }

    session = SessionLocal()
    try:
        while True:  # Main book loop
            table_choice = Prompt.ask(
                "Which table would you like to modify?",
                choices=list(models.keys())
            )

            model = models[table_choice]
            current_book = None  # Track the current book for related updates

            while True:  # Table/entry loop
                entry = search_and_select_entry(session, model, console)

                if not entry:
                    if not Confirm.ask("Try another search?", default=False):
                        break
                    continue

                # Update the entry
                if isinstance(entry, Book):
                    current_book = entry  # Store current book for related updates
                    data = get_book_input(session, is_new=False, existing_book=entry)
                elif isinstance(entry, Reading):
                    data = get_reading_input(session, entry.book_id, existing_reading=entry)
                else:  # Inventory
                    data = get_inventory_input(session, entry.book_id, existing_inventory=entry)

                # Update the entry
                if data:
                    for key, value in data.items():
                        if value is not None:
                            setattr(entry, key, value)

                    session.commit()
                    console.print("\n[bold green]Database updated successfully![/bold green]")
                    display_entry_card(entry, model)

                    # Prompt for updating another table for the same book
                    other_tables = [t for t in models.keys() if t != table_choice]
                    console.print("\nUpdate another table for this book? (Enter table name or press Enter to skip)")
                    console.print(f"Available tables: {', '.join(other_tables)}")
                    next_table = Prompt.ask("Table", choices=other_tables + [''], default='')

                    if next_table:
                        table_choice = next_table
                        model = models[table_choice]

                        # Search for related entries
                        search_term = current_book.title if current_book else ""
                        console.print(f"\nSearching for '{search_term}' in {table_choice} table...")
                        entries = search_entries(session, model, search_term, search_by_id=False)

                        if entries:
                            display_search_results(entries, model, session)
                        else:
                            console.print(f"\nNo existing {table_choice} entry found for '{search_term}'")
                            if current_book and Confirm.ask("Would you like to create a new entry?"):
                                if model == Reading:
                                    data = get_reading_input(session, current_book.id)
                                else:  # Inventory
                                    data = get_inventory_input(session, current_book.id)

                                if data:
                                    new_entry = model(**data)
                                    session.add(new_entry)
                                    session.commit()
                                    console.print("\n[bold green]New entry created successfully![/bold green]")
                                    display_entry_card(new_entry, model)
                else:
                    console.print("No changes made", style="yellow")

                if not Confirm.ask("\nWould you like to update another entry?", default=True):
                    return

    except Exception as e:
        console.print(f"Error: {str(e)}", style=error_style)
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()


