from datetime import date
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from .base import Base

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
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