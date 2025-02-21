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

if __name__ == "__main__":
    query_database()