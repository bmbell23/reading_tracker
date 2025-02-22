import sys
from datetime import datetime
from pathlib import Path
from scripts.utils.paths import find_project_root

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(project_root))

from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from src.models.inventory import Inventory
from sqlalchemy import func

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
        print("Invalid date format. Please use YYYY-MM-DD")
        return None

def parse_boolean(value):
    """Parse string to boolean"""
    return value.lower() in ('yes', 'true', 't', 'y', '1')

def get_book_input(session, is_new=True):
    """Get book information from user"""
    data = {}
    existing_book = None

    if not is_new:
        title = input("Enter book title to update: ")
        existing_book = session.query(Book).filter(Book.title == title).first()
        if not existing_book:
            print(f"Book '{title}' not found")
            return None
        data['id'] = existing_book.id
    else:
        data['id'] = get_next_id(session, Book)

    fields = [
        ('title', str, "Title"),
        ('author', str, "Author"),
        ('word_count', int, "Word count"),
        ('page_count', int, "Page count"),
        ('date_published', parse_date, "Date published (YYYY-MM-DD)"),
        ('author_gender', str, "Author gender"),
        ('series', str, "Series"),
        ('series_number', int, "Series number"),
        ('genre', str, "Genre")
    ]

    for field, type_conv, prompt in fields:
        if not is_new:
            current_value = getattr(existing_book, field)
            if input(f"Update {prompt}? (current: {current_value}) (y/n): ").lower() != 'y':
                continue

        while True:
            if is_new:
                value = input(f"{prompt}: ")
            else:
                value = input(f"{prompt} (current: {current_value}): ")

            if not value:
                data[field] = None
                break
            try:
                data[field] = type_conv(value)
                break
            except ValueError:
                print(f"Invalid input for {field}. Please try again.")

    return data

def get_reading_input(session, book_id, existing_reading=None):
    """Get reading information from user"""
    data = {
        'id': existing_reading.id if existing_reading else get_next_id(session, Reading),
        'book_id': book_id
    }

    fields = [
        ('id_previous', int, "Previous reading ID"),
        ('media', str, "Media type (Physical/Kindle/Audio)"),
        ('date_started', parse_date, "Date started (YYYY-MM-DD)"),
        ('date_finished_actual', parse_date, "Date finished (YYYY-MM-DD)")
    ]

    for field, type_conv, prompt in fields:
        while True:
            current_value = getattr(existing_reading, field) if existing_reading else None
            value = input(f"{prompt} (current: {current_value}): ")
            if not value:
                data[field] = None
                break
            try:
                data[field] = type_conv(value)
                break
            except ValueError:
                print(f"Invalid input for {field}. Please try again.")

    return data

def get_inventory_input(session, book_id, existing_inventory=None):
    """Get inventory information from user"""
    data = {
        'id': existing_inventory.id if existing_inventory else get_next_id(session, Inventory),
        'book_id': book_id
    }

    fields = [
        ('owned_audio', parse_boolean, "Owned in audio?"),
        ('owned_kindle', parse_boolean, "Owned in Kindle?"),
        ('owned_physical', parse_boolean, "Owned in physical?"),
        ('date_purchased', parse_date, "Date purchased (YYYY-MM-DD)"),
        ('location', str, "Location")
    ]

    for field, type_conv, prompt in fields:
        while True:
            current_value = getattr(existing_inventory, field) if existing_inventory else None
            if field in ['owned_audio', 'owned_kindle', 'owned_physical']:
                value = input(f"{prompt} (current: {current_value}) (y/n): ")
            else:
                value = input(f"{prompt} (current: {current_value}): ")

            if not value and field not in ['owned_audio', 'owned_kindle', 'owned_physical']:
                data[field] = None
                break
            try:
                data[field] = type_conv(value)
                break
            except ValueError:
                print(f"Invalid input for {field}. Please try again.")

    return data

def main():
    session = SessionLocal()
    try:
        # Determine if updating existing or creating new
        action = input("Are you (1) updating an existing book or (2) adding a new book? (1/2): ")
        is_new = action == "2"

        # Get book information
        book_data = get_book_input(session, is_new)
        if not book_data:
            return

        if is_new:
            book = Book(**book_data)
            session.add(book)
            existing_reading = None
            existing_inventory = None
        else:
            # Replace Query.get() with Session.get()
            book = session.get(Book, book_data['id'])
            for key, value in book_data.items():
                if value is not None:
                    setattr(book, key, value)
            # Get existing reading and inventory if any
            existing_reading = session.query(Reading).filter(Reading.book_id == book.id).first()
            existing_inventory = session.query(Inventory).filter(Inventory.book_id == book.id).first()

        # Ask about reading entry
        if input("Add/Update reading entry? (y/n): ").lower() == 'y':
            reading_data = get_reading_input(session, book_data['id'], existing_reading)
            if existing_reading:
                for key, value in reading_data.items():
                    if value is not None:
                        setattr(existing_reading, key, value)
            else:
                reading = Reading(**reading_data)
                session.add(reading)

        # Ask about inventory entry
        if input("Add/Update inventory entry? (y/n): ").lower() == 'y':
            inventory_data = get_inventory_input(session, book_data['id'], existing_inventory)
            if existing_inventory:
                for key, value in inventory_data.items():
                    if value is not None:
                        setattr(existing_inventory, key, value)
            else:
                inventory = Inventory(**inventory_data)
                session.add(inventory)

        session.commit()
        print("Database updated successfully!")

    except Exception as e:
        print(f"Error: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
