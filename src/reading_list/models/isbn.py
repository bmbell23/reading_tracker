from sqlalchemy import Column, Integer, String, Boolean, Date
from .base import Base

class ISBN(Base):
    __tablename__ = 'isbn'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author_name_first = Column(String)
    author_name_second = Column(String)
    author_gender = Column(String)
    page_count = Column(Integer)
    date_published = Column(Date)
    has_cover = Column(Boolean)
    isbn_10 = Column(String(10))
    isbn_13 = Column(String(13))
    asin = Column(String(10))
    source = Column(String)

    def __repr__(self):
        return f"<ISBN(id={self.id}, title='{self.title}', isbn_10='{self.isbn_10}', isbn_13='{self.isbn_13}')>"
