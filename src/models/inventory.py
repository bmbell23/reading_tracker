from datetime import date
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, VARCHAR
from sqlalchemy.orm import relationship
from .base import Base

class Inventory(Base):
    __tablename__ = 'inv'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    owned_audio = Column(Boolean, default=False)
    owned_kindle = Column(Boolean, default=False)
    owned_physical = Column(Boolean, default=False)
    date_purchased = Column(Date)
    location = Column(VARCHAR)
    read_status = Column(VARCHAR)
    read_count = Column(Integer)
    isbn_10 = Column(VARCHAR(10))
    isbn_13 = Column(VARCHAR(13))

    # Relationships
    book = relationship("Book", backref="inventory_items")

    @property
    def owned_overall(self):
        return any([self.owned_audio, self.owned_kindle, self.owned_physical])
