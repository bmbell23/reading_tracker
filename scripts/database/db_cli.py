"""
Unified CLI tool for database operations.

This script provides a command-line interface for common database operations
including viewing current readings, managing inventory, and cleaning up invalid
or empty database entries.

Usage:
    python db_cli.py [options]

Options:
    --current          Show all current reading sessions
    --inventory [type] Show inventory (all/physical/kindle/audio)
    --cleanup-books    Remove books with missing essential data
    --cleanup-empty    Remove empty database entries

Examples:
    python db_cli.py --current
    python db_cli.py --inventory kindle
    python db_cli.py --cleanup-books
"""
import argparse
from datetime import date
from collections import defaultdict
from tabulate import tabulate

from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from src.models.inventory import Inventory
from sqlalchemy import or_, and_

class DatabaseCLI:
    def __init__(self):
        self.session = SessionLocal()

    def cleanup_books(self):
        """Remove books with missing essential data"""
        try:
            invalid_books = self.session.query(Book).filter(
                or_(
                    Book.title == None,
                    Book.title == '',
                    Book.title.is_(None)
                )
            ).all()

            print("\nBooks to be deleted:")
            for book in invalid_books:
                print(f"ID: {book.id}, Title: {book.title}, Author: {book.author}")

            if invalid_books:
                confirm = input("\nDo you want to delete these books? (yes/no): ")
                if confirm.lower() == 'yes':
                    for book in invalid_books:
                        self.session.delete(book)
                    self.session.commit()
                    print(f"\nDeleted {len(invalid_books)} invalid books")
                else:
                    print("\nDeletion cancelled")
            else:
                print("\nNo invalid books found")

        except Exception as e:
            print(f"Error: {str(e)}")
            self.session.rollback()

    def show_current_readings(self):
        """Display currently active reading sessions"""
        try:
            current_readings = (
                self.session.query(Reading)
                .join(Book)
                .filter(
                    Reading.date_started.isnot(None),
                    Reading.date_finished_actual.is_(None)
                )
                .all()
            )

            if not current_readings:
                print("\nNo current readings found")
                return

            # Group readings by media type
            readings_by_media = defaultdict(list)
            for reading in current_readings:
                media = reading.media or "Unknown"
                author = f"{reading.book.author_name_first or ''} {reading.book.author_name_second or ''}".strip()

                reading_data = [
                    reading.book.title,
                    author,
                    reading.date_started.strftime("%Y-%m-%d"),
                    reading.date_est_end.strftime("%Y-%m-%d") if reading.date_est_end else "N/A"
                ]
                readings_by_media[media].append(reading_data)

            # Display readings grouped by media
            for media, readings in readings_by_media.items():
                print(f"\n{media} Books:")
                print(tabulate(
                    readings,
                    headers=["Title", "Author", "Started", "Est. Completion"],
                    tablefmt="grid"
                ))

        except Exception as e:
            print(f"Error: {str(e)}")

    def show_inventory(self, format_type=None):
        """Display inventory information"""
        try:
            query = self.session.query(Inventory).join(Book)

            if format_type:
                if format_type == 'physical':
                    query = query.filter(Inventory.owned_physical == True)
                elif format_type == 'kindle':
                    query = query.filter(Inventory.owned_kindle == True)
                elif format_type == 'audio':
                    query = query.filter(Inventory.owned_audio == True)

            inventory = query.all()

            if not inventory:
                print("\nNo inventory items found")
                return

            inventory_data = []
            for item in inventory:
                formats = []
                if item.owned_physical: formats.append("Physical")
                if item.owned_kindle: formats.append("Kindle")
                if item.owned_audio: formats.append("Audio")

                inventory_data.append([
                    item.book.title,
                    ", ".join(formats),
                    item.location or "N/A",
                    item.read_count or 0
                ])

            print("\nInventory:")
            print(tabulate(
                inventory_data,
                headers=["Title", "Formats", "Location", "Times Read"],
                tablefmt="grid"
            ))

        except Exception as e:
            print(f"Error: {str(e)}")

    def cleanup_empty_entries(self):
        """Remove empty database entries"""
        try:
            # Clean up Books table
            empty_books = self.session.query(Book).filter(
                Book.title.is_(None),
                Book.author_name_first.is_(None),
                Book.author_name_second.is_(None),
                Book.word_count.is_(None),
                Book.page_count.is_(None),
                Book.date_published.is_(None),
                Book.author_gender.is_(None),
                Book.series.is_(None),
                Book.series_number.is_(None),
                Book.genre.is_(None)
            ).all()

            # Clean up Readings table
            empty_readings = self.session.query(Reading).filter(
                Reading.id_previous.is_(None),
                Reading.media.is_(None),
                Reading.date_started.is_(None),
                Reading.date_finished_actual.is_(None),
                Reading.rating_enjoyment.is_(None)
            ).all()

            # Clean up Inventory table
            empty_inventory = self.session.query(Inventory).filter(
                Inventory.owned_audio.is_(False),
                Inventory.owned_kindle.is_(False),
                Inventory.owned_physical.is_(False),
                Inventory.date_purchased.is_(None),
                Inventory.location.is_(None),
                Inventory.read_status.is_(None),
                Inventory.read_count.is_(None)
            ).all()

            print("\nEmpty entries found:")
            print(f"Books: {len(empty_books)}")
            print(f"Readings: {len(empty_readings)}")
            print(f"Inventory: {len(empty_inventory)}")

            if empty_books or empty_readings or empty_inventory:
                confirm = input("\nDo you want to delete these empty entries? (yes/no): ")
                if confirm.lower() == 'yes':
                    for book in empty_books:
                        self.session.delete(book)
                    for reading in empty_readings:
                        self.session.delete(reading)
                    for inv in empty_inventory:
                        self.session.delete(inv)

                    self.session.commit()
                    print("\nEmpty entries deleted successfully!")
                else:
                    print("\nDeletion cancelled")
            else:
                print("\nNo empty entries found")

        except Exception as e:
            print(f"Error: {str(e)}")
            self.session.rollback()

    def close(self):
        """Close the database session"""
        self.session.close()

def main():
    parser = argparse.ArgumentParser(description="Database CLI tool for Reading List")
    parser.add_argument('--current', action='store_true', help='Show current readings')
    parser.add_argument('--inventory', nargs='?', const='all',
                       choices=['all', 'physical', 'kindle', 'audio'],
                       help='Show inventory (optionally filtered by format)')
    parser.add_argument('--cleanup-books', action='store_true', help='Clean up invalid books')
    parser.add_argument('--cleanup-empty', action='store_true', help='Clean up empty entries')

    args = parser.parse_args()

    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return

    db_cli = DatabaseCLI()
    try:
        if args.current:
            db_cli.show_current_readings()
        if args.inventory:
            format_type = None if args.inventory == 'all' else args.inventory
            db_cli.show_inventory(format_type)
        if args.cleanup_books:
            db_cli.cleanup_books()
        if args.cleanup_empty:
            db_cli.cleanup_empty_entries()
    finally:
        db_cli.close()

if __name__ == "__main__":
    main()
