from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class ISBN(Base):
    __tablename__ = 'isbn'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    isbn_10 = Column(String(10))
    isbn_13 = Column(String(13))
    format = Column(String(50))
    edition = Column(String(100))
    language = Column(String(50))
    publisher = Column(String(100))
    publication_date = Column(Date)
    print_run = Column(Integer)
    binding = Column(String(50))
    height = Column(Numeric(4,2))
    width = Column(Numeric(4,2))
    thickness = Column(Numeric(4,2))
    weight = Column(Integer)
    pages = Column(Integer)
    cover_image_url = Column(String(255))
    description = Column(Text)

    # Relationship with Book
    book = relationship("Book", back_populates="isbns")

    def __repr__(self):
        return f"<ISBN(id={self.id}, isbn_13={self.isbn_13})>"














