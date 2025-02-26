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

class DatabaseUpdater:
    def __init__(self):
        self.console = Console()
        self.session = SessionLocal()
        self.error_style = Style(color="red", bold=True)
        self.success_style = Style(color="green", bold=True)
        self.header_style = Style(color="blue", bold=True)

        self.models = {
            "books": Book,
            "read": Reading,
            "inv": Inventory
        }

        self.current_book = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_next_id(self, model):
        max_id = self.session.query(func.max(model.id)).scalar()
        return 1 if max_id is None else max_id + 1

    def search_entries(self, model, search_term, search_by_id=False):
        if search_by_id:
            try:
                id_num = int(search_term)
                return self.session.query(model).filter(model.id == id_num).all()
            except ValueError:
                return []

        return self.session.query(model).filter(
            or_(
                model.title.ilike(f"%{search_term}%") if hasattr(model, 'title') else False,
                model.book.has(Book.title.ilike(f"%{search_term}%")) if hasattr(model, 'book') else False
            )
        ).all()

    def prompt_for_data(self, model, existing_entry=None, book_id=None):
        """Generic method to handle data input for any model"""
        data = {'id': existing_entry.id if existing_entry else self.get_next_id(model)}
        if book_id:
            data['book_id'] = book_id

        field_configs = self.get_field_configs(model)

        console.print(Panel(f"{model.__name__} Information", style=self.header_style))

        for field, type_conv, prompt in field_configs:
            while True:
                try:
                    current_value = getattr(existing_entry, field) if existing_entry else None

                    if isinstance(type_conv, bool):
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
                    self.console.print(f"Invalid input for {field}. Please try again.", style=self.error_style)

        return data

    def get_field_configs(self, model):
        """Return field configurations based on model type"""
        if model == Book:
            return [
                ('title', str, "Title"),
                ('author', str, "Author"),
                ('word_count', int, "Word count"),
                ('page_count', int, "Page count"),
                ('date_published', self.parse_date, "Date published (YYYY-MM-DD)"),
                ('author_gender', str, "Author gender"),
                ('series', str, "Series"),
                ('series_number', int, "Series number"),
                ('genre', str, "Genre")
            ]
        elif model == Reading:
            return [
                ('id_previous', int, "Previous reading ID"),
                ('media', str, "Media type [cyan](Physical/Kindle/Audio)[/cyan]"),
                ('date_started', self.parse_date, "Date started [cyan](YYYY-MM-DD)[/cyan]"),
                ('date_finished_actual', self.parse_date, "Date finished [cyan](YYYY-MM-DD)[/cyan]")
            ]
        else:  # Inventory
            return [
                ('owned_audio', bool, "Owned in audio?"),
                ('owned_kindle', bool, "Owned in Kindle?"),
                ('owned_physical', bool, "Owned in physical?"),
                ('date_purchased', self.parse_date, "Date purchased [cyan](YYYY-MM-DD)[/cyan]"),
                ('location', str, "Location")
            ]

    def update_entry(self, entry, data):
        """Update entry with new data and commit to database"""
        for key, value in data.items():
            if value is not None:
                setattr(entry, key, value)

        self.session.commit()
        self.console.print("\n[bold green]Database updated successfully![/bold green]")
        self.display_entry_card(entry)

    def create_new_entry(self, model, data):
        """Create new entry and commit to database"""
        new_entry = model(**data)
        self.session.add(new_entry)
        self.session.commit()
        self.console.print("\n[bold green]New entry created successfully![/bold green]")
        self.display_entry_card(new_entry)
        return new_entry

    @staticmethod
    def parse_date(date_str):
        """Parse date string into datetime object"""
        return datetime.strptime(date_str, "%Y-%m-%d").date()

    def run(self):
        """Main execution loop"""
        self.console.print(Panel("Database Update Utility", style=self.header_style))

        try:
            while True:
                table_choice = Prompt.ask(
                    "Which table would you like to modify?",
                    choices=list(self.models.keys())
                )

                if not self.handle_table_update(table_choice):
                    break

        except Exception as e:
            self.console.print(f"Error: {str(e)}", style=self.error_style)
            self.session.rollback()

def main():
    with DatabaseUpdater() as updater:
        updater.run()

if __name__ == "__main__":
    main()
