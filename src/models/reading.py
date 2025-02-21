from datetime import date
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..utils.constants import READING_SPEEDS, DEFAULT_WPD
from .base import Base

class Reading(Base):
    __tablename__ = 'read'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    id_previous = Column(Integer, ForeignKey('read.id'))
    media = Column(String)
    date_started = Column(Date)
    date_finished_actual = Column(Date)
    _days_estimate = Column('days_estimate', Integer)
    _days_elapsed_to_read = Column('days_elapsed_to_read', Integer)
    _days_to_read_delta_from_estimate = Column('days_to_read_delta_from_estimate', Integer)

    # Ratings
    rating_horror = Column(Float)
    rating_spice = Column(Float)
    rating_world_building = Column(Float)
    rating_writing = Column(Float)
    rating_characters = Column(Float)
    rating_readability = Column(Float)
    rating_enjoyment = Column(Float)

    # Relationships
    book = relationship("Book", backref="readings")
    previous_reading = relationship("Reading", remote_side=[id], backref="subsequent_readings")

    @property
    def days_estimate(self):
        """Calculate estimated days to read based on book word count and media type"""
        if not self.book or not self.book.word_count or not self.media:
            return None

        media_lower = self.media.lower()
        words_per_day = READING_SPEEDS.get(media_lower, DEFAULT_WPD)
        return int(self.book.word_count / words_per_day)

    @days_estimate.setter
    def days_estimate(self, value):
        """Set the days_estimate value"""
        self._days_estimate = value

    @property
    def date_finished_estimate(self):
        """
        Calculate estimated finish date based on start date and days_estimate
        Returns: Date or None if start date or days_estimate is not available
        """
        if not self.date_started or not self.days_estimate:
            return None

        from datetime import timedelta
        return self.date_started + timedelta(days=self.days_estimate)

    @property
    def days_elapsed_to_read(self):
        """Calculate actual days taken to read"""
        if not self.date_started or not self.date_finished_actual:
            return None
        return (self.date_finished_actual - self.date_started).days

    @days_elapsed_to_read.setter
    def days_elapsed_to_read(self, value):
        self._days_elapsed_to_read = value

    @property
    def days_to_read_delta_from_estimate(self):
        """Calculate difference between estimated and actual days to read"""
        if not self.days_estimate or not self.days_elapsed_to_read:
            return None
        return self.days_elapsed_to_read - self.days_estimate

    @days_to_read_delta_from_estimate.setter
    def days_to_read_delta_from_estimate(self, value):
        self._days_to_read_delta_from_estimate = value
