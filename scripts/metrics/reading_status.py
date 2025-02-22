import sys
from pathlib import Path
from datetime import date, timedelta
from rich.console import Console
from rich.text import Text
from rich.table import Table
from scripts.utils.paths import find_project_root
from src.queries.reading_queries import ReadingQueries

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(Path(project_root)))

console = Console()

class ReadingStatus:
    def __init__(self):
        self.queries = ReadingQueries()
        self.today = date.today()

    def _format_author(self, book):
        """Format author name from book object"""
        return f"{book.author_name_first or ''} {book.author_name_second or ''}".strip()

    def _calculate_progress(self, reading, days_elapsed, days_remaining):
        """Calculate and format reading progress"""
        if days_remaining is not None and reading.book.page_count:
            total_days = days_elapsed + days_remaining
            progress_pct = (days_elapsed / total_days) if total_days > 0 else 0
            est_pages = int(progress_pct * reading.book.page_count)
            return f"{progress_pct:.0%} (p. {est_pages})"
        return "Unknown"

    def _format_reading_row(self, reading, is_current=True):
        """Format a reading entry into a table row"""
        author = self._format_author(reading.book)

        if is_current:
            days_elapsed = (self.today - reading.date_started).days
            days_remaining = reading.days_estimate - days_elapsed if reading.days_estimate else None
            est_end_date = self.today + timedelta(days=days_remaining) if days_remaining else None
            progress_str = self._calculate_progress(reading, days_elapsed, days_remaining)
            start_date = reading.date_started
        else:
            days_elapsed = "-"
            days_remaining = reading.days_estimate if reading.days_estimate else None
            est_end_date = reading.date_est_end
            progress_str = "-"
            start_date = reading.date_est_start

        # Define color based on media type
        if reading.media.lower() == 'audio':
            color = 'orange1'
        elif reading.media.lower() == 'hardcover':
            color = 'purple'
        elif reading.media.lower() == 'kindle':
            color = 'blue'
        else:
            color = 'white'

        return [
            reading.media,
            reading.book.title,
            author,
            start_date.strftime('%Y-%m-%d'),
            progress_str,
            str(days_elapsed),
            str(days_remaining or 'Unknown'),
            est_end_date.strftime('%Y-%m-%d') if est_end_date else 'Unknown'
        ], color

    def _create_table(self, title):
        """Create a rich table with standard headers"""
        table = Table(title=title, show_header=True, header_style="bold white")
        table.add_column("Format", justify="center")
        table.add_column("Title", justify="left")
        table.add_column("Author", justify="left")
        table.add_column("Start\nDate", justify="center")
        table.add_column("Est.\nProgress", justify="center")
        table.add_column("Days\nElapsed", justify="center")
        table.add_column("Days\nto Finish", justify="center")
        table.add_column("Est.\nEnd Date", justify="center")
        return table

    def show_current_readings(self):
        """Display currently active reading sessions"""
        results = self.queries.get_current_unfinished_readings()
        table = self._create_table("Current Reading Sessions")

        # Sort results by media type and title
        sorted_results = sorted(results, key=lambda x: (x.media.lower(), x.book.title))

        for reading in sorted_results:
            if reading.date_started > self.today:
                continue
            row_data, color = self._format_reading_row(reading)
            table.add_row(*row_data, style=color)

        console.print("\n")
        console.print(table)
        console.print("\n")

    def show_upcoming_readings(self):
        """Display upcoming reading sessions for the next 30 days"""
        results = self.queries.get_upcoming_readings()
        table = self._create_table("Upcoming Reading Sessions (Next 30 Days)")

        # Sort results by estimated start date
        sorted_results = sorted(results, key=lambda x: x.date_est_start or date.max)

        for reading in sorted_results:
            if not reading.date_est_start:
                continue
            row_data, color = self._format_reading_row(reading, is_current=False)
            table.add_row(*row_data, style=color)

        console.print("\n")
        if sorted_results:
            console.print(table)
        else:
            console.print("[yellow]No upcoming reading sessions found for the next 30 days.[/yellow]")
        console.print("\n")

def main():
    status = ReadingStatus()
    status.show_current_readings()
    status.show_upcoming_readings()

if __name__ == "__main__":
    main()
