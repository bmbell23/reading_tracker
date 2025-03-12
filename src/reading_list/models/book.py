from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, VARCHAR
from sqlalchemy.orm import relationship
from .base import Base

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(VARCHAR, nullable=False)
    author_name_first = Column(VARCHAR)
    author_name_second = Column(VARCHAR)
    author_gender = Column(VARCHAR)
    word_count = Column(Integer)
    page_count = Column(Integer)
    date_published = Column(Date)
    series = Column(VARCHAR)
    series_number = Column(Integer)
    genre = Column(VARCHAR)
    cover = Column(Boolean, nullable=False, default=False)
    isbn_id = Column(Integer)

    # Define relationships without circular references
    readings = relationship("Reading", back_populates="book")
    inventory = relationship("Inventory", back_populates="book")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}')>"
