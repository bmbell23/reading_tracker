"""
Database Update Utility
======================

A command-line interface for updating book-related database entries.
"""
from typing import List, Optional, Any, Dict, Type
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from pathlib import Path

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
                table.add_row(
                    str(entry.id),
                    entry.book.title,
                    str(entry.date_started) if entry.date_started else "Not started",
                    str(entry.date_finished_actual) if entry.date_finished_actual else "In progress",
                    entry.media or "Unknown",
                    str(entry.days_elapsed_to_read) if entry.days_elapsed_to_read else "-"
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
        date_fields = {'date_published', 'date_started', 'date_finished'}
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
            'date_finished': 'Finish Date (YYYY-MM-DD)',
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

    def get_input_data(self, is_new: bool = False, existing: Any = None) -> Dict[str, Any]:
        """Get user input based on model type"""
        data = {}

        fields = self.get_field_config(self.model)

        for field_name, prompt, field_type in fields:
            current = getattr(existing, field_name) if existing else None
            if Prompt.ask(f"Update {prompt}? [cyan](current: {current})[/cyan]", choices=['y', 'n'], default='n') == 'y':
                value = Prompt.ask(prompt)
                # Convert empty string to None
                if value.strip() == '':
                    value = None
                # Convert numeric strings to integers for appropriate fields
                elif field_name in {'page_count', 'word_count', 'series_number'}:
                    try:
                        value = int(value)
                    except ValueError:
                        StyleConfig.console.print(f"Invalid number format for {field_name}: {value}", style=StyleConfig.ERROR)
                        continue
                data[field_name] = value
                StyleConfig.console.print(f"Debug: Added {field_name} = {value} to update data")

        StyleConfig.console.print(f"Debug: Final update data: {data}")

        if self.model == Book:
            return self.editor.get_book_data(data, existing)
        elif self.model == Reading:
            return self.editor.get_reading_data(data, existing.book_id, existing)
        elif self.model == Inventory:
            return self.editor.get_inventory_data(data, existing.book_id, existing)

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

    def _handle_table_updates(self, table_choice: str):
        """Handle updates for a specific table"""
        handler = self.handlers[table_choice]

        while True:
            search_term = Prompt.ask("Enter ID or title to search (or 'back' to return)")
            if search_term.lower() == 'back':
                break

            entries = handler.search(search_term)
            if not entries:
                StyleConfig.console.print("No matching entries found", style=StyleConfig.ERROR)
                continue

            handler.display_results(entries)
            if len(entries) == 1 and Prompt.ask("Update this entry?", choices=['y', 'n'], default='n') == 'y':
                self._update_entry(entries[0], handler)

    def _update_entry(self, entry: Any, handler: ModelHandler):
        """Update a single entry"""
        try:
            # Display current entry
            StyleConfig.console.print("\n[bold cyan]Current Entry:[/bold cyan]")
            handler.display_results([entry])

            # Get new data
            data = handler.get_input_data(is_new=False, existing=entry)
            if not data:
                StyleConfig.console.print("No changes made", style="yellow")
                return

            # Create a temporary copy of the entry to show preview
            preview_entry = type(entry)()
            for attr, value in vars(entry).items():
                if not attr.startswith('_'):  # Skip SQLAlchemy internal attributes
                    setattr(preview_entry, attr, value)

            # Apply proposed changes to preview
            for key, value in data.items():
                if value is not None:
                    setattr(preview_entry, key, value)

            # Show preview
            StyleConfig.console.print("\n[bold cyan]Preview of Changes:[/bold cyan]")
            handler.display_results([preview_entry])

            # Confirm changes
            if Confirm.ask("\nApply these changes?", default=False):
                updated_entry = self.editor.update_entry(type(entry), entry.id, data)
                StyleConfig.console.print("\n[bold green]Database updated successfully![/bold green]")

                if isinstance(entry, Book):
                    self._prompt_related_updates(entry.id)
            else:
                StyleConfig.console.print("Update cancelled", style="yellow")

        except Exception as e:
            self.session.rollback()
            StyleConfig.console.print(f"Error updating entry: {str(e)}", style=StyleConfig.ERROR)

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

def main():
    """Main entry point"""
    StyleConfig.console.print(Panel("Database Update Utility", style=StyleConfig.HEADER))
    updater = DatabaseUpdater()
    updater.run()

if __name__ == "__main__":
    main()
