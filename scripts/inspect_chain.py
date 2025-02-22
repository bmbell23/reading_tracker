import sys
import os
from datetime import date, timedelta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book
from sqlalchemy import inspect

def print_reading_details(reading):
    """Print all fields from a reading entry"""
    # Get all columns from the Reading model
    mapper = inspect(Reading)
    attributes = [column.key for column in mapper.attrs]

    print(f"\nBook ID: {reading.id}")
    print(f"Title: {reading.book.title}")

    # Print all fields
    for attr in attributes:
        # Skip internal SQLAlchemy attributes and the book relationship
        if not attr.startswith('_') and attr != 'book':
            value = getattr(reading, attr)
            print(f"{attr}: {value}")
    print("-" * 50)

def inspect_chain_around_book(title_fragment, num_books=10):
    session = SessionLocal()
    try:
        # Find the target book's reading
        target = (session.query(Reading)
                 .join(Book)
                 .filter(Book.title.ilike(f"%{title_fragment}%"))
                 .first())

        if not target:
            print(f"No reading found with title containing '{title_fragment}'")
            return

        print(f"\nFound target book: {target.book.title} (ID: {target.id})")

        # Collect books before
        before_chain = []
        current = target
        for _ in range(num_books):
            if not current.id_previous:
                break
            current = session.get(Reading, current.id_previous)
            if current:
                before_chain.insert(0, current)

        # Collect books after
        after_chain = []
        current = target
        for _ in range(num_books):
            next_reading = (session.query(Reading)
                          .filter(Reading.id_previous == current.id)
                          .first())
            if not next_reading:
                break
            after_chain.append(next_reading)
            current = next_reading

        # Print the chain
        print("\n=== BOOKS BEFORE TARGET ===")
        for reading in before_chain:
            print_reading_details(reading)

        print("\n=== TARGET BOOK ===")
        print_reading_details(target)
        print("=" * 50)

        print("\n=== BOOKS AFTER TARGET ===")
        for reading in after_chain:
            print_reading_details(reading)

    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python inspect_chain.py <book_title_fragment>")
        sys.exit(1)
    inspect_chain_around_book(sys.argv[1])
