from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Inventory(Base):
    __tablename__ = 'inv'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    owned_audio = Column(Boolean)
    owned_kindle = Column(Boolean)
    owned_physical = Column(Boolean)
    date_purchased = Column(Date)
    location = Column(String)
    read_status = Column(String)
    read_count = Column(Integer)
    isbn_10 = Column(String(10))
    isbn_13 = Column(String(13))

    book = relationship("Book", back_populates="inventory")
