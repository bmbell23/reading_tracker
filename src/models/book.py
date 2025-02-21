from datetime import date
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from .base import Base

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author_name_first = Column(String)
    author_name_second = Column(String)
    word_count = Column(Integer)
    page_count = Column(Integer)
    date_published = Column(Date)
    author_gender = Column(String)
    series = Column(String)
    series_number = Column(Integer)
    genre = Column(String)

    @property
    def words_per_page(self):
        return self.word_count / self.page_count if self.page_count else None

    @property
    def year_published(self):
        return self.date_published.year if self.date_published else None

    @property
    def author(self):
        """Returns the full author name in 'First Last' format"""
        if not self.author_name_second and not self.author_name_first:
            return None
        name_parts = [self.author_name_first, self.author_name_second]
        return " ".join(filter(None, name_parts))

    @property
    def author_sorted(self):
        """Returns the author name in 'Last, First' format"""
        if not self.author_name_second:
            return self.author_name_first
        if not self.author_name_first:
            return self.author_name_second
        return f"{self.author_name_second}, {self.author_name_first}"
