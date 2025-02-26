#!/usr/bin/env python3
"""
Database Update Utility
======================

A command-line interface for updating book-related database entries across three tables:
- books: Main book information
- read: Reading session records
- inv: Book inventory tracking
"""
from datetime import datetime
from typing import List, Optional, Type, Dict, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from pathlib import Path

from reading_list.models.base import engine, SessionLocal
from reading_list.models.book import Book
from reading_list.models.reading import Reading
from reading_list.models.inventory import Inventory
from reading_list.models import Base

def verify_db():
    """Verify database exists at expected location"""
    expected_path = Path(engine.url.database)
    if not expected_path.exists():
        StyleConfig.console.print(
            f"Database not found at: {expected_path}",
            style=StyleConfig.ERROR
        )
        raise FileNotFoundError(f"Database not found at: {expected_path}")

class StyleConfig:
    """Centralized style configuration"""
    ERROR = Style(color="red", bold=True)
    SUCCESS = Style(color="green", bold=True)
    HEADER = Style(color="blue", bold=True)
    console = Console()

class ModelHandler:
    """Base class for handling different model types"""
    def __init__(self, model: Type, session: Session):
        self.model = model
        self.session = session
        self.styles = StyleConfig()

    def search(self, search_term: str, search_by_id: bool = False) -> List:
        """Base search method to be overridden by subclasses"""
        if search_by_id:
            try:
                entry = self.session.query(self.model).filter(
                    self.model.id == int(search_term)
                ).first()
                return [entry] if entry else []
            except ValueError:
                return []
        return []

    def get_table_columns(self) -> List[Dict[str, str]]:
        """Define table columns for display"""
        raise NotImplementedError

    def get_row_data(self, entry: Any) -> List[str]:
        """Get row data for display"""
        raise NotImplementedError

    def display_results(self, entries: List) -> None:
        """Display search results in a table"""
        table = Table(title=f"Search Results ({len(entries)} found)")

        for col in self.get_table_columns():
            table.add_column(**col)

        for entry in entries:
            table.add_row(*self.get_row_data(entry))

        StyleConfig.console.print(table)

    def get_input_data(self, is_new: bool = False, existing: Any = None) -> Dict:
        """Get input data for create/update"""
        raise NotImplementedError

class BookHandler(ModelHandler):
    def search(self, search_term: str, search_by_id: bool = False) -> List:
        if result := super().search(search_term, search_by_id):
            return result

        return self.session.query(self.model).filter(
            or_(
                Book.title.ilike(f"%{search_term}%"),
                Book.author_name_first.ilike(f"%{search_term}%"),
                Book.author_name_second.ilike(f"%{search_term}%")
            )
        ).all()

    def get_table_columns(self) -> List[Dict[str, str]]:
        return [
            {"header": "ID", "justify": "right", "style": "cyan"},
            {"header": "Title", "style": "magenta"},
            {"header": "Author", "style": "green"},
            {"header": "Published", "style": "blue"}
        ]

    def get_row_data(self, entry: Book) -> List[str]:
        author = f"{entry.author_name_first} {entry.author_name_second}".strip()
        return [
            str(entry.id),
            entry.title,
            author,
            str(entry.date_published) if entry.date_published else ''
        ]

    def get_input_data(self, is_new: bool = False, existing: Any = None) -> Dict:
        """Get book information from user"""
        data = {}
        fields = [
            ('title', str, "Title"),
            ('author_name_first', str, "Author first name"),
            ('author_name_second', str, "Author last name"),
            ('word_count', int, "Word count"),
            ('page_count', int, "Page count"),
            ('date_published', self._parse_date, "Date published (YYYY-MM-DD)"),
            ('author_gender', str, "Author gender"),
            ('series', str, "Series"),
            ('series_number', int, "Series number"),
            ('genre', str, "Genre")
        ]

        StyleConfig.console.print(Panel("Book Information", style=StyleConfig.HEADER))

        for field, type_conv, prompt in fields:
            current_value = getattr(existing, field) if existing else None
            while True:
                try:
                    value = Prompt.ask(
                        f"{prompt} [cyan](current: {current_value})[/cyan]" if existing else prompt
                    )
                    if not value:  # Skip if empty
                        break
                    data[field] = type_conv(value)
                    break
                except ValueError:
                    StyleConfig.console.print(
                        f"Invalid input for {field}. Please try again.",
                        style=StyleConfig.ERROR
                    )

        return data

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parse date string in YYYY-MM-DD format"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD")

class ReadingHandler(ModelHandler):
    def search(self, search_term: str, search_by_id: bool = False) -> List:
        if search_by_id:
            try:
                entry = self.session.query(self.model).filter(
                    self.model.id == int(search_term)
                ).first()
                return [entry] if entry else []
            except ValueError:
                return []

        return (self.session.query(self.model)
                .join(Book)
                .filter(Book.title.ilike(f"%{search_term}%"))
                .all())

    def get_table_columns(self) -> List[Dict[str, str]]:
        return [
            {"header": "ID", "justify": "right", "style": "cyan"},
            {"header": "Book", "style": "magenta"},
            {"header": "Started", "style": "green"},
            {"header": "Finished", "style": "green"},
            {"header": "Media", "style": "blue"},
            {"header": "Ratings", "style": "yellow"}
        ]

    def get_row_data(self, entry: Reading) -> List[str]:
        book = self.session.get(Book, entry.book_id)
        ratings = []
        if entry.rating_enjoyment:
            ratings.append(f"Enjoyment: {entry.rating_enjoyment}")
        if entry.rating_writing:
            ratings.append(f"Writing: {entry.rating_writing}")

        return [
            str(entry.id),
            book.title if book else "Unknown",
            str(entry.date_started) if entry.date_started else '',
            str(entry.date_finished_actual) if entry.date_finished_actual else '',
            str(entry.media) if entry.media else '',
            ", ".join(ratings) if ratings else ''
        ]

    def get_input_data(self, is_new: bool = False, existing: Any = None) -> Dict:
        """Get reading information from user"""
        data = {}
        fields = [
            ('date_started', self._parse_date, "Date started (YYYY-MM-DD)"),
            ('date_finished_actual', self._parse_date, "Date finished (YYYY-MM-DD)"),
            ('media', str, "Media type"),
            ('rating_enjoyment', int, "Enjoyment rating (1-5)"),
            ('rating_writing', int, "Writing rating (1-5)")
        ]

        StyleConfig.console.print(Panel("Reading Information", style=StyleConfig.HEADER))

        for field, type_conv, prompt in fields:
            current_value = getattr(existing, field) if existing else None
            while True:
                try:
                    value = Prompt.ask(
                        f"{prompt} [cyan](current: {current_value})[/cyan]" if existing else prompt
                    )
                    if not value:  # Skip if empty
                        break
                    data[field] = type_conv(value)
                    break
                except ValueError:
                    StyleConfig.console.print(
                        f"Invalid input for {field}. Please try again.",
                        style=StyleConfig.ERROR
                    )

        return data

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parse date string in YYYY-MM-DD format"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD")

class InventoryHandler(ModelHandler):
    def search(self, search_term: str, search_by_id: bool = False) -> List:
        if result := super().search(search_term, search_by_id):
            return result

        return self.session.query(self.model).join(Book).filter(
            Book.title.ilike(f"%{search_term}%")
        ).all()

    def get_table_columns(self) -> List[Dict[str, str]]:
        return [
            {"header": "ID", "justify": "right", "style": "cyan"},
            {"header": "Book", "style": "magenta"},
            {"header": "Formats", "style": "green"},
            {"header": "Location", "style": "green"}
        ]

    def get_row_data(self, entry: Inventory) -> List[str]:
        book = self.session.get(Book, entry.book_id)
        formats = []
        if entry.owned_physical:
            formats.append("Physical")
        if entry.owned_kindle:
            formats.append("Kindle")
        if entry.owned_audio:
            formats.append("Audio")

        return [
            str(entry.id),
            book.title if book else "Unknown",
            ", ".join(formats),
            entry.location or ''
        ]

    def get_input_data(self, is_new: bool = False, existing: Any = None) -> Dict:
        """Get inventory information from user"""
        data = {}
        fields = [
            ('owned_physical', self._parse_bool, "Own physical copy?"),
            ('owned_kindle', self._parse_bool, "Own Kindle copy?"),
            ('owned_audio', self._parse_bool, "Own audio copy?"),
            ('location', str, "Location"),
            ('read_count', int, "Read count")
        ]

        StyleConfig.console.print(Panel("Inventory Information", style=StyleConfig.HEADER))

        for field, type_conv, prompt in fields:
            current_value = getattr(existing, field) if existing else None
            while True:
                try:
                    if field in ['owned_physical', 'owned_kindle', 'owned_audio']:
                        value = Prompt.ask(
                            f"{prompt} [cyan](current: {current_value})[/cyan]" if existing else prompt,
                            choices=['y', 'n'],
                            default='n'
                        )
                        data[field] = value.lower() == 'y'
                        break
                    else:
                        value = Prompt.ask(
                            f"{prompt} [cyan](current: {current_value})[/cyan]" if existing else prompt
                        )
                        if not value:  # Skip if empty
                            break
                        data[field] = type_conv(value)
                        break
                except ValueError:
                    StyleConfig.console.print(
                        f"Invalid input for {field}. Please try again.",
                        style=StyleConfig.ERROR
                    )

        return data

    def _parse_bool(self, value: str) -> bool:
        """Parse string to boolean"""
        return value.lower() in ('yes', 'true', 't', 'y', '1')

class DatabaseUpdater:
    """Main class for handling database updates"""
    def __init__(self):
        verify_db()  # Verify database exists before creating session
        self.session = SessionLocal()
        self.handlers = {
            "books": BookHandler(Book, self.session),
            "read": ReadingHandler(Reading, self.session),
            "inv": InventoryHandler(Inventory, self.session)
        }
        self.current_book = None

    def run(self):
        """Main run loop with clean exit"""
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

            # Try to parse as ID first
            try:
                id_entries = handler.search(search_term, search_by_id=True)
            except ValueError:
                id_entries = []

            # Always search titles too
            title_entries = handler.search(search_term, search_by_id=False)

            # Combine results, removing duplicates
            entries = list({entry.id: entry for entry in (id_entries + title_entries)}.values())

            if not entries:
                StyleConfig.console.print("No matching entries found", style=StyleConfig.ERROR)
                continue

            handler.display_results(entries)

            if len(entries) == 1:
                if Prompt.ask("Is this the correct entry? [y/n]", choices=['y', 'n'], default='y') == 'y':
                    self._update_entry(entries[0], handler)
            else:
                entry_id = Prompt.ask("Enter the ID of the correct entry (or press Enter to search again)")
                if entry_id:
                    selected = next((e for e in entries if str(e.id) == entry_id), None)
                    if selected and Prompt.ask("Is this the correct entry? [y/n]", choices=['y', 'n'], default='y') == 'y':
                        self._update_entry(selected, handler)

            if not Prompt.ask("Would you like to update another entry?", choices=['y', 'n'], default='n') == 'y':
                break

    def get_reading_input(self, book_id: int, existing_reading: Optional[Reading] = None) -> Dict[str, Any]:
        """Get reading information from user"""
        data = {
            'id': existing_reading.id if existing_reading else None,
            'book_id': book_id
        }

        fields = [
            ('id_previous', int, "Previous reading ID"),
            ('media', str, "Media type [cyan](Hardcover/Kindle/Audio)[/cyan]"),
            ('date_started', self._parse_date, "Date started [cyan](YYYY-MM-DD)[/cyan]"),
            ('date_finished_actual', self._parse_date, "Date finished [cyan](YYYY-MM-DD)[/cyan]"),
            ('rating_horror', float, "Horror rating (0-10)"),
            ('rating_spice', float, "Spice rating (0-10)"),
            ('rating_world_building', float, "World Building rating (0-10)"),
            ('rating_writing', float, "Writing rating (0-10)"),
            ('rating_characters', float, "Characters rating (0-10)"),
            ('rating_readability', float, "Readability rating (0-10)"),
            ('rating_enjoyment', float, "Enjoyment rating (0-10)"),
            ('rank', int, "Rank"),
            ('days_estimate', int, "Estimated days to read"),
            ('days_elapsed_to_read', int, "Actual days taken to read"),
            ('date_est_start', self._parse_date, "Estimated start date [cyan](YYYY-MM-DD)[/cyan]"),
            ('date_est_end', self._parse_date, "Estimated end date [cyan](YYYY-MM-DD)[/cyan]")
        ]

        StyleConfig.console.print("\nPress Enter to skip a field (keep current value)", style=StyleConfig.HEADER)
        for field, type_conv, prompt in fields:
            while True:
                try:
                    current_value = getattr(existing_reading, field) if existing_reading else None
                    if Prompt.ask(
                        f"Update {prompt}? [cyan](current: {current_value})[/cyan]",
                        choices=['y', 'n'],
                        default='n'
                    ) == 'y':
                        value = Prompt.ask(f"New value for {prompt}")
                        if value:
                            data[field] = type_conv(value)
                    else:
                        data[field] = current_value
                    break
                except ValueError:
                    StyleConfig.console.print(f"Invalid input for {field}. Please try again.", style=StyleConfig.ERROR)

        return data

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parse date string in YYYY-MM-DD format"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            StyleConfig.console.print("Invalid date format. Please use YYYY-MM-DD", style=StyleConfig.ERROR)
            return None

    def get_book_input(self, is_new: bool = True, existing_book: Optional[Book] = None) -> Dict[str, Any]:
        """Get book information from user"""
        data = {}
        if not is_new and existing_book:
            data['id'] = existing_book.id

        fields = [
            ('title', str, "Title"),
            ('author_name_first', str, "Author first name"),
            ('author_name_second', str, "Author last name"),
            ('author_gender', str, "Author gender"),
            ('word_count', int, "Word count"),
            ('page_count', int, "Page count"),
            ('date_published', self._parse_date, "Date published (YYYY-MM-DD)"),
            ('series', str, "Series"),
            ('series_number', int, "Series number"),
            ('genre', str, "Genre"),
            ('has_cover', bool, "Has cover? (y/n)"),
            ('isbn_id', int, "ISBN ID")
        ]

        StyleConfig.console.print("\nPress Enter to skip a field (keep current value)", style=StyleConfig.HEADER)
        for field, type_conv, prompt in fields:
            while True:
                try:
                    current_value = getattr(existing_book, field) if existing_book else None
                    if Prompt.ask(
                        f"Update {prompt}? [cyan](current: {current_value})[/cyan]",
                        choices=['y', 'n'],
                        default='n'
                    ) == 'y':
                        if type_conv == bool:
                            value = Prompt.ask(f"New value for {prompt}", choices=['y', 'n'], default='n')
                            data[field] = value.lower() == 'y'
                        else:
                            value = Prompt.ask(f"New value for {prompt}")
                            if value:
                                data[field] = type_conv(value)
                    else:
                        data[field] = current_value
                    break
                except ValueError:
                    StyleConfig.console.print(f"Invalid input for {field}. Please try again.", style=StyleConfig.ERROR)

        return data

    def get_inventory_input(self, book_id: int, existing_inventory: Optional[Inventory] = None) -> Dict[str, Any]:
        """Get inventory information from user"""
        data = {
            'id': existing_inventory.id if existing_inventory else None,
            'book_id': book_id
        }

        fields = [
            ('owned_audio', bool, "Owned in audio?"),
            ('owned_kindle', bool, "Owned in Kindle?"),
            ('owned_physical', bool, "Owned in physical?"),
            ('date_purchased', self._parse_date, "Date purchased [cyan](YYYY-MM-DD)[/cyan]"),
            ('location', str, "Location"),
            ('read_status', str, "Read status"),
            ('read_count', int, "Read count"),
            ('isbn_10', str, "ISBN-10"),
            ('isbn_13', str, "ISBN-13")
        ]

        StyleConfig.console.print("\nPress Enter to skip a field (keep current value)", style=StyleConfig.HEADER)
        for field, type_conv, prompt in fields:
            while True:
                try:
                    current_value = getattr(existing_inventory, field) if existing_inventory else None
                    if Prompt.ask(
                        f"Update {prompt}? [cyan](current: {current_value})[/cyan]",
                        choices=['y', 'n'],
                        default='n'
                    ) == 'y':
                        if type_conv == bool:
                            value = Prompt.ask(f"New value for {prompt}", choices=['y', 'n'], default='n')
                            data[field] = value.lower() == 'y'
                        else:
                            value = Prompt.ask(f"New value for {prompt}")
                            if value:
                                data[field] = type_conv(value)
                    else:
                        data[field] = current_value
                    break
                except ValueError:
                    StyleConfig.console.print(f"Invalid input for {field}. Please try again.", style=StyleConfig.ERROR)

        return data

    def _update_entry(self, entry: Any, handler: ModelHandler):
        """Update an entry with proper error handling"""
        try:
            if isinstance(entry, Book):
                data = self.get_book_input(is_new=False, existing_book=entry)
            elif isinstance(entry, Reading):
                data = self.get_reading_input(entry.book_id, existing_reading=entry)
            else:  # Inventory
                data = self.get_inventory_input(entry.book_id, existing_inventory=entry)

            if data:
                for key, value in data.items():
                    if value is not None:
                        setattr(entry, key, value)

                self.session.commit()
                StyleConfig.console.print("\n[bold green]Database updated successfully![/bold green]")
                handler.display_results([entry])
            else:
                StyleConfig.console.print("No changes made", style="yellow")

        except Exception as e:
            self.session.rollback()
            StyleConfig.console.print(f"Error updating entry: {str(e)}", style=StyleConfig.ERROR)

    def search_and_select_entry(self, handler: ModelHandler) -> Optional[Any]:
        """Search for and select an entry to update"""
        search_term = Prompt.ask("Enter ID or title to search (or 'back' to return)")

        if search_term.lower() == 'back':
            return None

        # Try ID search first
        id_entries = handler.search(search_term, search_by_id=True)
        # Then title search
        title_entries = handler.search(search_term, search_by_id=False)

        # Combine results, removing duplicates
        entries = list({entry.id: entry for entry in (id_entries + title_entries)}.values())

        if not entries:
            StyleConfig.console.print("No matching entries found", style=StyleConfig.ERROR)
            return None

        handler.display_results(entries)

        if len(entries) == 1:
            if Prompt.ask(
                "Is this the correct entry?",
                choices=['y', 'n'],
                default='y'
            ) == 'y':
                return entries[0]
        else:
            entry_id = Prompt.ask("Enter the ID of the entry to update (or press Enter to cancel)")
            if entry_id:
                return next((e for e in entries if str(e.id) == entry_id), None)

        return None

    def update_entry(self, entry: Any, handler: ModelHandler, table_type: str) -> None:
        """Update the selected entry"""
        try:
            if isinstance(entry, Book):
                self.current_book = entry

            data = handler.get_input_data(is_new=False, existing=entry)
            if data:
                for key, value in data.items():
                    if value is not None:
                        setattr(entry, key, value)

                self.session.commit()
                StyleConfig.console.print("\n[bold green]Database updated successfully![/bold green]")
                handler.display_results([entry])

                # Prompt for updating related entries
                if isinstance(entry, Book):
                    other_tables = [t for t in self.handlers.keys() if t != table_type]
                    StyleConfig.console.print("\nUpdate related entries? (Enter table name or press Enter to skip)")
                    StyleConfig.console.print(f"Available tables: {', '.join(other_tables)}")

                    next_table = Prompt.ask(
                        "Table",
                        choices=other_tables + [''],
                        default=''
                    )

                    if next_table:
                        related_handler = self.handlers[next_table]
                        if related_entry := self.search_and_select_entry(related_handler):
                            self.update_entry(related_entry, related_handler, next_table)
            else:
                StyleConfig.console.print("No changes made", style="yellow")

        except Exception as e:
            self.session.rollback()
            StyleConfig.console.print(f"Error updating entry: {str(e)}", style=StyleConfig.ERROR)

def main():
    """Main entry point"""
    StyleConfig.console.print(Panel(
        "Database Update Utility",
        style=StyleConfig.HEADER
    ))

    updater = DatabaseUpdater()
    try:
        while True:
            table_choice = Prompt.ask(
                "Which table would you like to modify? (or 'exit' to quit)",
                choices=["books", "read", "inv", "exit"],
                default="exit"
            )

            if table_choice == 'exit':
                StyleConfig.console.print("[green]Goodbye![/green]")
                break

            handler = updater.handlers[table_choice]
            if entry := updater.search_and_select_entry(handler):
                updater.update_entry(entry, handler, table_choice)

            if not Prompt.ask(
                "Would you like to continue?",
                choices=['y', 'n'],
                default='n'
            ) == 'y':
                break

    except KeyboardInterrupt:
        StyleConfig.console.print("\n[green]Goodbye![/green]")
    finally:
        updater.session.close()

if __name__ == "__main__":
    main()
