"""Repository for reading-related database operations."""
from datetime import date
from typing import List
from sqlalchemy.orm import Session
from ..models.base import engine
from ..models.reading import Reading
from ..models.book import Book

class ReadingRepository:
    def __init__(self):
        """Initialize reading repository."""
        self.session = Session(engine)

    def get_current_readings(self) -> List[Reading]:
        """Get list of current unfinished readings."""
        return (
            self.session.query(Reading)
            .join(Book)
            .filter(Reading.date_finished_actual.is_(None))
            .filter(Reading.date_started <= date.today())
            .all()
        )

    def get_upcoming_readings(self) -> List[Reading]:
        """Get list of upcoming readings."""
        return (
            self.session.query(Reading)
            .join(Book)
            .filter(Reading.date_finished_actual.is_(None))
            .filter(Reading.date_est_start > date.today())  # Changed from date_started to date_est_start
            .order_by(Reading.date_est_start)
            .all()
        )

    def __del__(self):
        """Ensure session is closed."""
        self.session.close()
