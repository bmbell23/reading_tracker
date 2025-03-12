from sqlalchemy import Column, Integer, String, Date, VARCHAR
from sqlalchemy.orm import relationship
from .base import Base

class ISBN(Base):
    __tablename__ = 'isbn'

    id = Column(Integer, primary_key=True)
    title = Column(VARCHAR, nullable=False)
    author_name_first = Column(VARCHAR)
    author_name_second = Column(VARCHAR)
    author_gender = Column(VARCHAR)
    page_count = Column(Integer)
    date_published = Column(Date)
    isbn_10 = Column(Integer)
    isbn_13 = Column(Integer)
    asin = Column(String(10))
    source = Column(VARCHAR)

    def __repr__(self):
        return f"<ISBN(id={self.id}, isbn_13='{self.isbn_13}')>"
