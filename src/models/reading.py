from datetime import date
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Reading(Base):
    __tablename__ = 'read'  # Changed from 'readings' to 'read'

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    previous_read_id = Column(Integer, ForeignKey('read.id'))  # Self-referential foreign key
    format = Column(String)
    date_started = Column(Date)
    date_finished_actual = Column(Date)
    date_finished_estimate = Column(Date)
    words_per_day_actual = Column(Float)
    words_per_day_goal = Column(Float)
    pages_per_day_goal = Column(Float)

    # Ratings
    rating_horror = Column(Float)
    rating_spice = Column(Float)
    rating_world_building = Column(Float)
    rating_writing = Column(Float)
    rating_characters = Column(Float)
    rating_readability = Column(Float)
    rating_enjoyment = Column(Float)
    rating_overall = Column(Float)

    # Relationships
    book = relationship("Book", backref="readings")
    previous_reading = relationship("Reading", remote_side=[id], backref="subsequent_readings")
