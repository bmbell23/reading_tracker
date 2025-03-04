"""Models for tracking reading status and progress."""
from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .base import engine
from .reading import Reading
from .book import Book
from sqlalchemy import and_

class ReadingStatus:
    def __init__(self):
        """Initialize reading status tracker."""
        self.session = Session(engine)

    def get_current_readings(self) -> List[Reading]:
        """Get list of current unfinished readings."""
        return (
            self.session.query(Reading)
            .join(Book)
            .filter(Reading.date_finished_actual.is_(None))  # This is correct from the Reading model
            .filter(Reading.date_started <= date.today())
            .all()
        )

    def get_upcoming_readings(self) -> List[Reading]:
        """Get list of upcoming readings starting within next 30 days."""
        today = date.today()
        thirty_days = today + timedelta(days=30)
        
        return (
            self.session.query(Reading)
            .join(Book)
            .filter(
                and_(
                    Reading.date_finished_actual.is_(None),  # Not finished
                    Reading.date_started.is_(None),  # Not started yet
                    Reading.date_est_start.isnot(None),  # Must have est. start date
                    Reading.date_est_start <= thirty_days,  # Must start WITHIN next 30 days
                )
            )
            .order_by(Reading.date_est_start)  # Order by estimated start date
            .all()  # Remove any limit
        )

    def __del__(self):
        """Ensure session is closed."""
        self.session.close()
