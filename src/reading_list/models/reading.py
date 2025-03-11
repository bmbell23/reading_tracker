from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Reading(Base):
    __tablename__ = 'read'

    id = Column(Integer, primary_key=True)
    id_previous = Column(Integer)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    media = Column(String)
    date_started = Column(Date)
    date_finished_actual = Column(Date)
    rating_horror = Column(Float)
    rating_spice = Column(Float)
    rating_world_building = Column(Float)
    rating_writing = Column(Float)
    rating_characters = Column(Float)
    rating_readability = Column(Float)
    rating_enjoyment = Column(Float)
    rank = Column(Integer)
    days_estimate = Column(Integer)
    days_elapsed_to_read = Column(Integer)
    days_to_read_delta_from_estimate = Column(Integer)
    date_est_start = Column(Date)
    date_est_end = Column(Date)
    reread = Column(Boolean, default=False)

    book = relationship("Book", back_populates="readings")
