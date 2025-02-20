from datetime import date
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Reading(Base):
    __tablename__ = 'readings'

    id = Column(Integer, primary_key=True)
    id_previous = Column(Integer, ForeignKey('readings.id'), nullable=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    format = Column(String)
    date_started = Column(Date)
    date_finished_actual = Column(Date)
    words_per_day_goal = Column(Integer)
    pages_per_day_goal = Column(Integer)

    # Ratings
    rating_horror = Column(Float)
    rating_spice = Column(Float)
    rating_world_building = Column(Float)
    rating_writing = Column(Float)
    rating_characters = Column(Float)
    rating_readability = Column(Float)
    rating_enjoyment = Column(Float)
    rating_overall = Column(Float)
    rating_over_rank = Column(Integer)
    rank = Column(Integer)

    # Relationships
    book = relationship("Book", backref="readings")
    previous_reading = relationship("Reading", remote_side=[id])

    @property
    def actual_days(self):
        if self.date_started and self.date_finished_actual:
            return (self.date_finished_actual - self.date_started).days
        return None