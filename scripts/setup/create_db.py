from src.models.base import Base, engine
from src.models.book import Book
from src.models.reading import Reading
from src.models.inventory import Inventory

def create_database():
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_database()
