import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from src.models.inventory import Inventory

def query_database():
    session = SessionLocal()
    try:
        # Example queries:

        # Get all books
        books = session.query(Book).all()
        print("\nAll Books:")
        for book in books:
            print(f"- {book.title} by {book.author}")

        # Get all readings with ratings
        readings = session.query(Reading).all()
        print("\nAll Readings:")
        for reading in readings:
            print(f"- {reading.book.title}: Enjoyment Rating: {reading.rating_enjoyment}")

        # Get inventory status
        inventory = session.query(Inventory).all()
        print("\nInventory:")
        for item in inventory:
            formats = []
            if item.owned_physical: formats.append("Physical")
            if item.owned_kindle: formats.append("Kindle")
            if item.owned_audio: formats.append("Audio")
            print(f"- {item.book.title}: Owned in {', '.join(formats)}")

    finally:
        session.close()

def cleanup_empty_entries():
    """Remove all entries that have an ID but all other fields are empty/null"""
    session = SessionLocal()
    try:
        # Clean up Books table
        empty_books = session.query(Book).filter(
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
        empty_readings = session.query(Reading).filter(
            Reading.id_previous.is_(None),
            Reading.media.is_(None),
            Reading.date_started.is_(None),
            Reading.date_finished_actual.is_(None),
            Reading.rating_horror.is_(None),
            Reading.rating_spice.is_(None),
            Reading.rating_world_building.is_(None),
            Reading.rating_writing.is_(None),
            Reading.rating_characters.is_(None),
            Reading.rating_readability.is_(None),
            Reading.rating_enjoyment.is_(None)
        ).all()

        # Clean up Inventory table
        empty_inventory = session.query(Inventory).filter(
            Inventory.owned_audio.is_(False),
            Inventory.owned_kindle.is_(False),
            Inventory.owned_physical.is_(False),
            Inventory.date_purchased.is_(None),
            Inventory.location.is_(None),
            Inventory.read_status.is_(None),
            Inventory.read_count.is_(None),
            Inventory.isbn_10.is_(None),
            Inventory.isbn_13.is_(None)
        ).all()

        # Print what will be deleted
        print("\nEmpty entries found:")
        print(f"Books: {len(empty_books)}")
        print(f"Readings: {len(empty_readings)}")
        print(f"Inventory: {len(empty_inventory)}")

        if empty_books or empty_readings or empty_inventory:
            confirm = input("\nDo you want to delete these empty entries? (yes/no): ")
            if confirm.lower() == 'yes':
                for book in empty_books:
                    session.delete(book)
                for reading in empty_readings:
                    session.delete(reading)
                for inv in empty_inventory:
                    session.delete(inv)

                session.commit()
                print("\nEmpty entries deleted successfully!")
            else:
                print("\nDeletion cancelled")
        else:
            print("\nNo empty entries found")

    except Exception as e:
        print(f"Error: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_empty_entries()
