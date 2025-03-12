from sqlalchemy.orm import relationship
from .base import Base, SessionLocal, engine
from .isbn import ISBN
from .book import Book
from .reading import Reading
from .inventory import Inventory

# Create all tables
Base.metadata.create_all(bind=engine)

__all__ = ['Base', 'SessionLocal', 'Book', 'Reading', 'Inventory', 'ISBN']
