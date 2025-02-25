from datetime import datetime, timedelta
from typing import List, Dict
from src.database import get_db

class StatisticsService:
    def __init__(self):
        self.db = get_db()

    def get_reading_streak(self) -> int:
        """Calculate current reading streak in days"""
        query = """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT date(date_read)
                FROM reading_progress
                WHERE date_read >= (
                    SELECT MAX(date_read)
                    FROM reading_progress
                    WHERE pages_read = 0
                )
            )
        """
        return self.db.execute(query).scalar()

    def get_monthly_progress(self) -> float:
        """Calculate progress towards monthly reading goal"""
        # Assuming monthly goal is stored in settings or calculated
        monthly_goal = 2000  # pages
        query = """
            SELECT SUM(pages_read)
            FROM reading_progress
            WHERE date_read >= date('now', 'start of month')
        """
        pages_read = self.db.execute(query).scalar() or 0
        return min(round((pages_read / monthly_goal) * 100, 1), 100)

    def get_reading_pace(self) -> float:
        """Calculate average daily reading pace"""
        query = """
            SELECT AVG(pages_read)
            FROM reading_progress
            WHERE date_read >= date('now', '-30 days')
        """
        return round(self.db.execute(query).scalar() or 0, 1)

    def get_pace_trend(self) -> str:
        """Determine if reading pace is increasing/decreasing"""
        recent_pace = self._get_average_pace(7)  # Last 7 days
        previous_pace = self._get_average_pace(7, offset=7)  # Previous 7 days

        if recent_pace > previous_pace * 1.1:
            return "increasing"
        elif recent_pace < previous_pace * 0.9:
            return "decreasing"
        return "steady"

    def get_trend_icon(self, trend: str) -> str:
        """Get icon for trend direction"""
        return {
            "increasing": "↗️",
            "decreasing": "↘️",
            "steady": "→"
        }.get(trend, "→")

    def get_streak_days(self) -> List[Dict]:
        """Get reading status for last 7 days"""
        days = []
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            query = """
                SELECT COUNT(*)
                FROM reading_progress
                WHERE date(date_read) = date(?)
                AND pages_read > 0
            """
            has_reading = self.db.execute(query, (date.date(),)).scalar() > 0
            days.append({
                'date': date.strftime('%Y-%m-%d'),
                'status': 'read' if has_reading else 'missed'
            })
        return days

    def _get_average_pace(self, days: int, offset: int = 0) -> float:
        """Get average reading pace for a period"""
        query = """
            SELECT AVG(pages_read)
            FROM reading_progress
            WHERE date_read >= date('now', ?)
            AND date_read < date('now', ?)
        """
        start = f'-{days + offset} days'
        end = f'-{offset} days' if offset > 0 else 'now'
        return self.db.execute(query, (start, end)).scalar() or 0
