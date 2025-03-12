"""
Database Update Utility
======================

A command-line interface for updating book-related database entries.
"""
from typing import List, Optional, Any, Dict, Type, Union
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from pathlib import Path
from datetime import datetime
from sqlalchemy import text, or_

from reading_list.models.base import engine, SessionLocal
from reading_list.models.book import Book
from reading_list.models.reading import Reading
from reading_list.models.inventory import Inventory
from reading_list.core.database.entry_editor import EntryEditor

class StyleConfig:
    """Centralized style configuration"""
    ERROR = Style(color="red", bold=True)
    SUCCESS = Style(color="green", bold=True)
    HEADER = Style(color="blue", bold=True)
    console = Console()

def verify_db():
    """Verify database exists at expected location"""
    expected_path = Path(engine.url.database)
    if not expected_path.exists():
        StyleConfig.console.print(
            f"Database not found at: {expected_path}",
            style=StyleConfig.ERROR
        )
        raise FileNotFoundError(f"Database not found at: {expected_path}")

class ModelHandler:
    """UI handler for different model types"""
    def __init__(self, model: type, editor: EntryEditor):
        self.model = model
        self.editor = editor
        self.styles = StyleConfig

    def search(self, search_term: str, search_by_id: bool = False) -> List:
        """Search using the editor"""
        return self.editor.search_entries(self.model, search_term, search_by_id)

    def display_results(self, entries: List):
        """Display search results in a table"""
        table = Table(title=f"{self.model.__name__} Search Results")

        # Add appropriate columns based on model
        if self.model == Book:
            table.add_column("ID", justify="right")
            table.add_column("Title")
            table.add_column("Author")
            for entry in entries:
                author = f"{entry.author_name_first} {entry.author_name_second}".strip()
                table.add_row(str(entry.id), entry.title, author)
        elif self.model == Reading:
            table.add_column("ID", justify="right")
            table.add_column("Book")
            table.add_column("Started")
            table.add_column("Finished")
            table.add_column("Media")
            table.add_column("Days")
            for entry in entries:
                # Handle both SQLAlchemy models and preview objects
                book_title = entry.book.title if hasattr(entry.book, 'title') else entry.book
                table.add_row(
                    str(getattr(entry, 'id', '')),
                    book_title,
                    str(getattr(entry, 'date_started', '')) if getattr(entry, 'date_started', None) else "Not started",
                    str(getattr(entry, 'date_finished_actual', '')) if getattr(entry, 'date_finished_actual', None) else "In progress",
                    getattr(entry, 'media', '') or "Unknown",
                    str(getattr(entry, 'days_elapsed_to_read', '')) if getattr(entry, 'days_elapsed_to_read', None) else "-"
                )
        elif self.model == Inventory:
            table.add_column("ID", justify="right")
            table.add_column("Book")
            table.add_column("Formats")
            for entry in entries:
                formats = []
                if entry.owned_physical: formats.append("Physical")
                if entry.owned_kindle: formats.append("Kindle")
                if entry.owned_audio: formats.append("Audio")
                table.add_row(str(entry.id), entry.book.title, ", ".join(formats))

        StyleConfig.console.print(table)

    def get_field_config(self, model: Type) -> List[tuple]:
        """Get field configuration based on model columns"""
        # Special handling for different field types
        boolean_fields = {'has_cover', 'completed', 'owned_physical', 'owned_kindle', 'owned_audio'}
        date_fields = {
            'date_published', 'date_started', 'date_finished_actual',
            'date_est_start', 'date_est_end'
        }  # Added date_finished_actual
        # Skip these fields as they're managed by SQLAlchemy or are foreign keys
        skip_fields = {'id', 'book_id', 'created_at', 'updated_at'}

        # Get readable names for fields
        field_names = {
            # Book fields
            'title': 'Title',
            'author_name_first': 'Author First Name',
            'author_name_second': 'Author Last Name',
            'date_published': 'Publication Date (YYYY-MM-DD)',
            'series': 'Series Name',
            'series_number': 'Series Number',
            'genre': 'Genre',
            'has_cover': 'Has Cover',
            'isbn_id': 'ISBN',
            'page_count': 'Page Count',
            # Reading fields
            'date_started': 'Start Date (YYYY-MM-DD)',
            'date_finished_actual': 'Finish Date (YYYY-MM-DD)',
            'date_est_start': 'Estimated Start Date (YYYY-MM-DD)',
            'date_est_end': 'Estimated End Date (YYYY-MM-DD)',
            'pages_read': 'Pages Read',
            'completed': 'Completed',
            # Inventory fields
            'owned_physical': 'Own Physical Copy',
            'owned_kindle': 'Own Kindle Copy',
            'owned_audio': 'Own Audio Copy',
            'location': 'Location'
        }

        fields = []
        for column in model.__table__.columns:
            if column.name in skip_fields:
                continue

            field_type = 'text'
            if column.name in boolean_fields:
                field_type = 'boolean'
            elif column.name in date_fields:
                field_type = 'date'

            fields.append((
                column.name,
                field_names.get(column.name, column.name.replace('_', ' ').title()),
                field_type
            ))

        return fields

    def get_update_data(self, existing: Any) -> Dict[str, Any]:
        """Get update data for an entry"""
        data = {}

        if isinstance(existing, Reading):
            fields = {
                'id_previous': ('number', existing.id_previous),
                'media': ('string', existing.media),
                'date_started': ('date', existing.date_started),
                'date_finished_actual': ('date', existing.date_finished_actual),
                'date_est_start': ('date', existing.date_est_start),
                'date_est_end': ('date', existing.date_est_end),
                'rating_horror': ('float', existing.rating_horror),
                'rating_spice': ('float', existing.rating_spice),
                'rating_world_building': ('float', existing.rating_world_building),
                'rating_writing': ('float', existing.rating_writing),
                'rating_characters': ('float', existing.rating_characters),
                'rating_readability': ('float', existing.rating_readability),
                'rating_enjoyment': ('float', existing.rating_enjoyment),
                'rank': ('number', existing.rank),
                'days_estimate': ('number', existing.days_estimate),
                'days_elapsed_to_read': ('number', existing.days_elapsed_to_read),
                'days_to_read_delta_from_estimate': ('number', existing.days_to_read_delta_from_estimate),
                'reread': ('boolean', existing.reread)
            }
        elif isinstance(existing, Book):
            fields = {
                'title': ('string', existing.title),
                'author_name_first': ('string', existing.author_name_first),
                'author_name_second': ('string', existing.author_name_second),
                'author_gender': ('string', existing.author_gender)
            }
        elif isinstance(existing, Inventory):
            fields = {
                'owned_physical': ('boolean', existing.owned_physical),
                'owned_kindle': ('boolean', existing.owned_kindle),
                'owned_audio': ('boolean', existing.owned_audio),
                'location': ('string', existing.location)
            }
        else:
            raise ValueError(f"Unsupported model type: {type(existing).__name__}")

        for field_name, (field_type, current_value) in fields.items():
            if Confirm.ask(f"Update {field_name.replace('_', ' ').title()}? (current: {current_value})", default=False):
                value = Prompt.ask(f"Enter new {field_name.replace('_', ' ').title()}")

                if not value.strip():
                    data[field_name] = None
                    continue

                if field_type == 'date':
                    try:
                        date_obj = datetime.strptime(value, '%Y-%m-%d').date()
                        data[field_name] = date_obj
                    except ValueError:
                        StyleConfig.console.print(f"[red]Invalid date format. Use YYYY-MM-DD[/red]")
                        continue
                elif field_type == 'boolean':
                    data[field_name] = value.lower() in ('y', 'yes', 'true', '1')
                elif field_type == 'number':
                    try:
                        data[field_name] = int(value)
                    except ValueError:
                        StyleConfig.console.print(f"[red]Invalid number format[/red]")
                        continue
                else:
                    data[field_name] = value

        return data

class DatabaseUpdater:
    """Main class for handling database updates"""
    def __init__(self):
        verify_db()
        self.session = SessionLocal()
        # Verify database connection
        try:
            # Try to execute a simple query
            book_count = self.session.query(Book).count()
            print(f"Successfully connected to database. Found {book_count} books.")
        except Exception as e:
            StyleConfig.console.print(f"Database connection error: {str(e)}", style=StyleConfig.ERROR)
            raise

        self.editor = EntryEditor(self.session)
        self.handlers = {
            "books": ModelHandler(Book, self.editor),
            "read": ModelHandler(Reading, self.editor),
            "inv": ModelHandler(Inventory, self.editor)
        }

    def run(self):
        """Main run loop"""
        try:
            while True:
                table_choice = Prompt.ask(
                    "Which table would you like to modify? (or 'exit' to quit)",
                    choices=list(self.handlers.keys()) + ['exit'],
                    default='exit'
                )

                if table_choice == 'exit':
                    StyleConfig.console.print("Goodbye!", style=StyleConfig.SUCCESS)
                    break

                self._handle_table_updates(table_choice)

        except KeyboardInterrupt:
            StyleConfig.console.print("\nGoodbye!", style=StyleConfig.SUCCESS)
        finally:
            self.session.close()

    def _get_book_id_from_user(self) -> Optional[int]:
        """Get book ID either directly or by searching title"""
        while True:
            search_term = Prompt.ask("Enter book ID or title to search (or 'back' to return)")

            if search_term.lower() == 'back':
                return None

            # Try to process as ID first
            try:
                book_id = int(search_term)
                book = self.session.get(Book, book_id)
                if book:
                    StyleConfig.console.print(f"Selected book: [green]{book.title}[/green]")
                    return book_id
                else:
                    StyleConfig.console.print(f"[red]Book ID {book_id} not found[/red]")
            except ValueError:
                # If not a valid ID, search by title
                results = self.editor.search_entries(Book, search_term)
                if results:
                    table = Table(title="Matching Books")
                    table.add_column("ID")
                    table.add_column("Title")
                    table.add_column("Author")

                    for book in results:
                        table.add_row(
                            str(book.id),
                            book.title,
                            f"{book.author_name_first} {book.author_name_second or ''}"
                        )

                    StyleConfig.console.print(table)

                    book_id = Prompt.ask("Enter ID of desired book (or 'back' to search again)")
                    if book_id.lower() == 'back':
                        continue

                    try:
                        book_id = int(book_id)
                        if any(b.id == book_id for b in results):
                            return book_id
                        else:
                            StyleConfig.console.print("[red]Invalid selection[/red]")
                    except ValueError:
                        StyleConfig.console.print("[red]Invalid ID format[/red]")
                else:
                    StyleConfig.console.print("[yellow]No matching books found[/yellow]")

    def _handle_table_updates(self, table_choice: str):
        """Handle updates for a specific table"""
        handler = self.handlers[table_choice]

        while True:
            action = Prompt.ask(
                "\nWhat would you like to do?",
                choices=["update", "new", "delete", "back"],
                default="back"
            )

            if action == 'back':
                break

            if action == 'new':
                if table_choice == 'read':
                    self._create_new_reading()
                elif table_choice == 'books':
                    self._create_new_book()
                elif table_choice == 'inv':
                    book_id = self._get_book_id_from_user()
                    if book_id is not None:
                        self._create_new_inventory(book_id)
                continue

            if action in ['update', 'delete']:
                search_term = Prompt.ask("Enter ID or title to search (or 'back' to return)")
                if search_term.lower() == 'back':
                    continue

                try:
                    search_id = int(search_term)
                    entry = self.session.get(handler.model, search_id)
                    if entry:
                        handler.display_results([entry])
                        if action == 'delete':
                            self._delete_entry(entry, handler)
                        else:
                            self._update_entry(entry, handler)
                    else:
                        StyleConfig.console.print(f"[red]No entry found with ID {search_id}[/red]")
                except ValueError:
                    results = handler.search_entries(search_term)
                    if results:
                        handler.display_results(results)
                        entry_id = Prompt.ask("Enter ID of entry to update")
                        try:
                            entry_id = int(entry_id)
                            entry = next((e for e in results if e.id == entry_id), None)
                            if entry:
                                if action == 'delete':
                                    self._delete_entry(entry, handler)
                                else:
                                    self._update_entry(entry, handler)
                            else:
                                StyleConfig.console.print("[red]Invalid selection[/red]")
                        except ValueError:
                            StyleConfig.console.print("[red]Invalid ID format[/red]")
                    else:
                        StyleConfig.console.print("[yellow]No matching entries found[/yellow]")

    def _update_entry(self, existing: Union[Book, Reading, Inventory], handler: ModelHandler):
        """Update a single entry"""
        try:
            new_data = {}
            table_name = existing.__tablename__

            # Get all columns for the table
            with engine.connect() as conn:
                columns = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()

            # Skip the ID column as it's primary key
            for col in columns[1:]:  # Skip first column (ID)
                col_name = col[1]  # Column name is second element
                current_value = getattr(existing, col_name, None)

                if Prompt.ask(
                    f"Update {col_name}? (current: {current_value})",
                    choices=['y', 'n'],
                    default='n'
                ) == 'y':
                    # Handle different column types
                    if col[2].upper() == 'DATE':
                        new_value = Prompt.ask(f"Enter new {col_name} (YYYY-MM-DD)")
                        try:
                            new_value = datetime.strptime(new_value, '%Y-%m-%d').date()
                        except ValueError:
                            new_value = None
                    elif col[2].upper() == 'BOOLEAN':
                        new_value = Prompt.ask(f"Enter new {col_name}", choices=['true', 'false']) == 'true'
                    elif col[2].upper().startswith('INTEGER'):
                        new_value = Prompt.ask(f"Enter new {col_name}")
                        try:
                            new_value = int(new_value) if new_value else None
                        except ValueError:
                            new_value = None
                    elif col[2].upper().startswith('FLOAT'):
                        new_value = Prompt.ask(f"Enter new {col_name}")
                        try:
                            new_value = float(new_value) if new_value else None
                        except ValueError:
                            new_value = None
                    else:  # VARCHAR/TEXT
                        new_value = Prompt.ask(f"Enter new {col_name}") or None

                    if new_value != current_value:
                        new_data[col_name] = new_value

            if new_data:
                # Display changes
                StyleConfig.console.print("\n[bold cyan]Changes to be made:[/bold cyan]")
                for field, new_value in new_data.items():
                    old_value = getattr(existing, field)
                    StyleConfig.console.print(f"{field}: [red]{old_value}[/red] → [green]{new_value}[/green]")

                if Prompt.ask("\nSave these changes?", choices=['y', 'n'], default='n') == 'y':
                    for field, value in new_data.items():
                        setattr(existing, field, value)
                    self.session.commit()
                    StyleConfig.console.print("[green]Changes saved successfully![/green]")
                else:
                    self.session.rollback()
                    StyleConfig.console.print("[yellow]Changes discarded[/yellow]")
            else:
                StyleConfig.console.print("\nNo changes made")

        except Exception as e:
            self.session.rollback()
            StyleConfig.console.print(f"[red]Error updating entry: {str(e)}[/red]")

    def _create_new_reading(self, book_id: int = None):
        """Create a new reading entry"""
        StyleConfig.console.print("\n[bold cyan]Creating New Reading Entry[/bold cyan]")

        # Get and validate book ID if not provided
        if book_id is None:
            while True:
                try:
                    book_id = int(Prompt.ask("Enter book ID"))
                    book = self.session.get(Book, book_id)
                    if book:
                        StyleConfig.console.print(f"Selected book: [green]{book.title}[/green]")
                        break
                    else:
                        StyleConfig.console.print(f"[red]Book ID {book_id} not found[/red]")
                except ValueError:
                    StyleConfig.console.print("[red]Please enter a valid number[/red]")
        else:
            book = self.session.get(Book, book_id)
            StyleConfig.console.print(f"Selected book: [green]{book.title}[/green]")

        # Get media type
        media = Prompt.ask("Enter media type", choices=["kindle", "hardcover", "audio"])

        # Get the next available read ID
        next_id = self.session.execute(text("SELECT MAX(id) FROM read")).scalar()
        next_id = (next_id or 0) + 1

        # Get the latest chain ID for this media type
        prev_id = self.session.execute(
            text("""
                SELECT id
                FROM read
                WHERE LOWER(media) = LOWER(:media)
                AND date_finished_actual IS NULL
                ORDER BY date_est_end DESC, id DESC
                LIMIT 1
            """),
            {"media": media}
        ).scalar()

        # Create new reading entry
        new_reading = Reading(
            id=next_id,
            book_id=book_id,
            media=media,
            id_previous=prev_id
        )

        self.session.add(new_reading)

        # Display preview
        StyleConfig.console.print("\n[bold cyan]New Reading Entry Preview:[/bold cyan]")
        StyleConfig.console.print(f"Read ID: [green]{next_id}[/green]")
        StyleConfig.console.print(f"Book: [green]{book.title}[/green]")
        StyleConfig.console.print(f"Media: [green]{media}[/green]")
        StyleConfig.console.print(f"Previous Read ID: [green]{prev_id or 'None'}[/green]")

        if Prompt.ask("\nSave this new reading entry?", choices=['y', 'n'], default='n') == 'y':
            self.session.commit()
            StyleConfig.console.print("[green]New reading entry created successfully![/green]")
        else:
            self.session.rollback()
            StyleConfig.console.print("[yellow]New reading entry discarded[/yellow]")

    def _create_new_book(self):
        """Create a new book entry"""
        StyleConfig.console.print("\n[bold cyan]Creating New Book Entry[/bold cyan]")

        # Get the next available book ID
        next_id = self.session.execute(text("SELECT MAX(id) FROM books")).scalar()
        next_id = (next_id or 0) + 1

        # Get required fields
        title = Prompt.ask("Enter book title")
        author_first = Prompt.ask("Enter author's first name")
        author_last = Prompt.ask("Enter author's last name")
        author_gender = Prompt.ask("Enter author's gender", choices=['M', 'F', 'O', ''], default='')

        # Optional numeric fields
        word_count = Prompt.ask("Enter word count (optional)", default="")
        if word_count and word_count.strip():
            try:
                word_count = int(word_count)
            except ValueError:
                word_count = None
        else:
            word_count = None

        page_count = Prompt.ask("Enter page count (optional)", default="")
        if page_count and page_count.strip():
            try:
                page_count = int(page_count)
            except ValueError:
                page_count = None
        else:
            page_count = None

        # Date field
        date_published = Prompt.ask("Enter publication date (YYYY-MM-DD) (optional)", default="")
        if date_published and date_published.strip():
            try:
                date_published = datetime.strptime(date_published, "%Y-%m-%d").date()
            except ValueError:
                date_published = None
        else:
            date_published = None

        # Series information
        series = Prompt.ask("Enter series name (optional)", default="")
        series_number = Prompt.ask("Enter series number (optional)", default="")
        if series_number and series_number.strip():
            try:
                series_number = int(series_number)
            except ValueError:
                series_number = None
        else:
            series_number = None

        # Other fields
        genre = Prompt.ask("Enter genre (optional)", default="")
        isbn = Prompt.ask("Enter ISBN (optional)", default="")
        if isbn and isbn.strip():
            try:
                isbn = int(isbn)
            except ValueError:
                isbn = None
        else:
            isbn = None

        # Create new book entry
        new_book = Book(
            id=next_id,
            title=title,
            author_name_first=author_first,
            author_name_second=author_last,
            author_gender=author_gender if author_gender else None,
            word_count=word_count,
            page_count=page_count,
            date_published=date_published,
            series=series if series else None,
            series_number=series_number,
            genre=genre if genre else None,
            cover=False,  # Default to False for new books
            isbn_id=isbn
        )

        # Display preview
        StyleConfig.console.print("\n[bold cyan]New Book Entry Preview:[/bold cyan]")
        StyleConfig.console.print(f"Book ID: [green]{next_id}[/green]")
        StyleConfig.console.print(f"Title: [green]{title}[/green]")
        StyleConfig.console.print(f"Author: [green]{author_first} {author_last}[/green]")
        if author_gender:
            StyleConfig.console.print(f"Author Gender: [green]{author_gender}[/green]")
        if word_count:
            StyleConfig.console.print(f"Word Count: [green]{word_count:,}[/green]")
        if page_count:
            StyleConfig.console.print(f"Page Count: [green]{page_count:,}[/green]")
        if date_published:
            StyleConfig.console.print(f"Published: [green]{date_published}[/green]")
        if series:
            StyleConfig.console.print(f"Series: [green]{series} #{series_number}[/green]")
        if genre:
            StyleConfig.console.print(f"Genre: [green]{genre}[/green]")
        if isbn:
            StyleConfig.console.print(f"ISBN: [green]{isbn}[/green]")

        if Prompt.ask("\nSave this new book entry?", choices=['y', 'n'], default='n') == 'y':
            self.session.add(new_book)
            self.session.commit()
            StyleConfig.console.print("[green]New book entry created successfully![/green]")

            # Ask if user wants to create related entries
            if Prompt.ask("Create inventory entry for this book?", choices=['y', 'n'], default='n') == 'y':
                self._create_new_inventory(new_book.id)

            if Prompt.ask("Create reading entry for this book?", choices=['y', 'n'], default='n') == 'y':
                self._create_new_reading(new_book.id)
        else:
            self.session.rollback()
            StyleConfig.console.print("[yellow]New book entry discarded[/yellow]")

    def _create_new_inventory(self, book_id: int):
        """Create a new inventory entry for a given book ID"""
        # First verify the book exists and get its title
        book = self.session.get(Book, book_id)
        if not book:
            StyleConfig.console.print(f"[red]Error: Book ID {book_id} not found[/red]")
            return

        StyleConfig.console.print(f"\n[bold cyan]Creating New Inventory Entry for:[/bold cyan]")
        StyleConfig.console.print(f"Book ID: [green]{book_id}[/green]")
        StyleConfig.console.print(f"Title: [green]{book.title}[/green]")

        # Get the next available inventory ID
        next_id = self.session.execute(text("SELECT MAX(id) FROM inv")).scalar()
        next_id = (next_id or 0) + 1

        # Get required fields
        owned_physical = Confirm.ask("Do you own the physical copy?")
        owned_kindle = Confirm.ask("Do you own the Kindle copy?")
        owned_audio = Confirm.ask("Do you own the audio copy?")

        # Optional fields
        location = Prompt.ask("Enter location (optional)", default="")

        # Create new inventory entry
        new_inventory = Inventory(
            id=next_id,
            book_id=book_id,
            owned_physical=owned_physical,
            owned_kindle=owned_kindle,
            owned_audio=owned_audio,
            location=location if location else None
        )

        # Display preview
        StyleConfig.console.print("\n[bold cyan]New Inventory Entry Preview:[/bold cyan]")
        StyleConfig.console.print(f"Inventory ID: [green]{next_id}[/green]")
        StyleConfig.console.print(f"Book ID: [green]{book_id}[/green]")
        StyleConfig.console.print(f"Physical Copy: [green]{'Yes' if owned_physical else 'No'}[/green]")
        StyleConfig.console.print(f"Kindle Copy: [green]{'Yes' if owned_kindle else 'No'}[/green]")
        StyleConfig.console.print(f"Audio Copy: [green]{'Yes' if owned_audio else 'No'}[/green]")
        if location:
            StyleConfig.console.print(f"Location: [green]{location}[/green]")

        if Prompt.ask("\nSave this new inventory entry?", choices=['y', 'n'], default='n') == 'y':
            self.session.add(new_inventory)
            self.session.commit()
            StyleConfig.console.print("[green]New inventory entry created successfully![/green]")
        else:
            self.session.rollback()
            StyleConfig.console.print("[yellow]New inventory entry discarded[/yellow]")

    def _prompt_related_updates(self, book_id: int):
        """Prompt for updating related entries"""
        related = self.editor.get_related_entries(book_id)
        if related['readings'] or related['inventory']:
            if Prompt.ask("Update related entries?", choices=['y', 'n'], default='n') == 'y':
                for entry_type, entries in related.items():
                    handler = self.handlers['read' if entry_type == 'readings' else 'inv']
                    handler.display_results(entries)
                    if entries and Prompt.ask(f"Update {entry_type}?", choices=['y', 'n'], default='n') == 'y':
                        self._update_entry(entries[0], handler)

    def _delete_entry(self, entry: Any, handler: ModelHandler):
        """Delete a single entry"""
        try:
            # Display current entry
            StyleConfig.console.print("\n[bold red]Entry to delete:[/bold red]")
            handler.display_results([entry])

            # Confirm deletion
            if Confirm.ask("\nAre you sure you want to delete this entry?", default=False):
                # Check for related entries if it's a Book
                if isinstance(entry, Book):
                    reading_count = self.session.query(Reading).filter_by(book_id=entry.id).count()
                    inventory_count = self.session.query(Inventory).filter_by(book_id=entry.id).count()

                    if reading_count > 0 or inventory_count > 0:
                        StyleConfig.console.print(
                            f"\n[yellow]Warning: This book has {reading_count} reading entries and {inventory_count} inventory entries.[/yellow]"
                        )
                        if not Confirm.ask("Delete anyway? This will remove all related entries", default=False):
                            StyleConfig.console.print("Deletion cancelled", style="yellow")
                            return

                # Perform the deletion
                self.session.delete(entry)
                self.session.commit()
                StyleConfig.console.print("\n[bold green]Entry deleted successfully![/bold green]")
            else:
                StyleConfig.console.print("Deletion cancelled", style="yellow")

        except Exception as e:
            self.session.rollback()
            StyleConfig.console.print(f"Error deleting entry: {str(e)}", style=StyleConfig.ERROR)

def main():
    """Main entry point"""
    StyleConfig.console.print(Panel("Database Update Utility", style=StyleConfig.HEADER))
    updater = DatabaseUpdater()
    updater.run()

if __name__ == "__main__":
    main()
