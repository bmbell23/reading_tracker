from sqlalchemy.orm import relationship
from .base import Base, SessionLocal, engine
from .isbn import ISBN
from .book import Book
from .reading import Reading
from .inventory import Inventory

# Initialize relationships after all models are defined
Book.isbn = relationship("ISBN", back_populates="book", uselist=False)
ISBN.book = relationship("Book", back_populates="isbn", uselist=False)

# Create all tables
Base.metadata.create_all(bind=engine)

__all__ = ['Base', 'SessionLocal', 'Book', 'Reading', 'Inventory', 'ISBN']
