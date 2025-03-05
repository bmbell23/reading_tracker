"""Models for tracking reading status and progress."""
from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .base import engine
from .reading import Reading
from .book import Book
from ..repositories.reading_repository import ReadingRepository

class ReadingStatus:
    def __init__(self):
        """Initialize reading status tracker."""
        self.session = Session(engine)
        self.repository = ReadingRepository()

    def _sort_readings(self, readings: List[Reading]) -> List[Reading]:
        """Standard sorting for readings: start date, estimated start, then title."""
        readings.sort(key=lambda x: (
            x.date_started or date.max,  # Actual start date (None sorts last)
            x.date_est_start or date.max,  # Estimated start date (None sorts last)
            x.book.title.lower()  # Title as tiebreaker
        ))
        return readings

    def get_current_readings(self) -> List[Reading]:
        """Get current readings with standard sorting."""
        readings = self.repository.get_current_readings()
        return self._sort_readings(readings)

    def get_upcoming_readings(self) -> List[Reading]:
        """Get upcoming readings with standard sorting."""
        readings = self.repository.get_upcoming_readings()
        return self._sort_readings(readings)

    def get_forecast_readings(self, days: int = 7) -> List[Reading]:
        """Get readings for forecast with standard sorting."""
        current_readings = self.get_current_readings()
        upcoming_readings = [r for r in self.get_upcoming_readings()
                            if r.date_est_start and r.date_est_start <= date.today() + timedelta(days=days)]

        all_readings = current_readings + upcoming_readings
        return self._sort_readings(all_readings)

    def __del__(self):
        """Ensure session is closed."""
        self.session.close()
