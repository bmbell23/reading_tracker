from sqlalchemy import Column, Integer, String, Date, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author_name_first = Column(String)
    author_name_second = Column(String)
    author_gender = Column(String)
    word_count = Column(Integer)
    page_count = Column(Integer)
    date_published = Column(Date)
    series = Column(String)
    series_number = Column(Integer)
    genre = Column(String)
    has_cover = Column(Boolean)
    cover = Column(Boolean, nullable=False, default=False)
    isbn_id = Column(Integer)

    readings = relationship("Reading", back_populates="book")
    inventory = relationship("Inventory", back_populates="book")
