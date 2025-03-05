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

    def get_forecast_readings(self, days: int = 7) -> List[Reading]:
        """Get readings for forecast, sorted by start date.

        Args:
            days: Number of days to look ahead for upcoming readings

        Returns:
            List of readings sorted by actual start date, then estimated start date
        """
        current_readings = self.get_current_readings()
        upcoming_readings = [r for r in self.get_upcoming_readings()
                            if r.date_est_start and r.date_est_start <= date.today() + timedelta(days=days)]

        all_readings = current_readings + upcoming_readings
        # Sort by actual start date first, then estimated start date, then title
        all_readings.sort(key=lambda x: (
            x.date_started or date.max,  # Actual start date (None sorts last)
            x.date_est_start or date.max,  # Estimated start date (None sorts last)
            x.book.title.lower()  # Title as tiebreaker
        ))

        return all_readings

    def __del__(self):
        """Ensure session is closed."""
        self.session.close()
