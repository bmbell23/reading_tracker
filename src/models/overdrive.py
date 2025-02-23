from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class OverdriveBook(Base):
    __tablename__ = 'overdrive_books'

    id = Column(Integer, primary_key=True)
    overdrive_id = Column(String, unique=True, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'))
    title = Column(String)
    author = Column(String)
    cover_url = Column(String)
    media_type = Column(String)  # ebook, audiobook
    isbn = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationships
    book = relationship("Book", backref="overdrive_books")

class OverdriveLoan(Base):
    __tablename__ = 'overdrive_loans'

    id = Column(Integer, primary_key=True)
    overdrive_book_id = Column(Integer, ForeignKey('overdrive_books.id'))
    expires_at = Column(DateTime)
    borrowed_at = Column(DateTime, default=datetime.utcnow)
    is_returned = Column(Boolean, default=False)

    # Relationships
    book = relationship("OverdriveBook", backref="loans")

class OverdriveHold(Base):
    __tablename__ = 'overdrive_holds'

    id = Column(Integer, primary_key=True)
    overdrive_book_id = Column(Integer, ForeignKey('overdrive_books.id'))
    position = Column(Integer)
    total_holds = Column(Integer)
    placed_at = Column(DateTime, default=datetime.utcnow)
    is_ready = Column(Boolean, default=False)
    estimated_wait_days = Column(Integer)

    # Relationships
    book = relationship("OverdriveBook", backref="holds")