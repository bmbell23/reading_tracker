from datetime import date
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    owned_audio = Column(Boolean, default=False)
    owned_kindle = Column(Boolean, default=False)
    owned_physical = Column(Boolean, default=False)
    date_purchased = Column(Date)
    location = Column(String)
    read_status = Column(String)
    read_count = Column(Integer, default=0)
    isbn_10 = Column(String(10))
    isbn_13 = Column(String(13))

    # Relationships
    book = relationship("Book", backref="inventory_items")

    @property
    def owned_overall(self):
        return any([self.owned_audio, self.owned_kindle, self.owned_physical])