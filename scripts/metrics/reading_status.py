import sys
from pathlib import Path
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from scripts.utils.paths import find_project_root
from src.queries.reading_queries import ReadingQueries
from src.utils.progress_calculator import calculate_reading_progress

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(Path(project_root)))

console = Console()

class ReadingStatus:
    """
    Manages and displays reading status information for current and upcoming books.

    This class provides functionality to:
    - Show currently active reading sessions with progress information
    - Display upcoming reading sessions for the next 30 days
    - Calculate and format reading progress metrics
    - Color-code different media types (audio, hardcover, kindle)
    """
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

            row_data = [
                reading.media,
                reading.book.title,
                author,
                start_date.strftime('%Y-%m-%d'),
                progress_str,
                str(days_elapsed),
                str(days_remaining or 'Unknown'),
                est_end_date.strftime('%Y-%m-%d') if est_end_date else 'Unknown'
            ]
        else:
            days_remaining = reading.days_estimate if reading.days_estimate else None
            est_end_date = reading.date_est_end
            start_date = reading.date_est_start

            row_data = [
                reading.media,
                reading.book.title,
                author,
                start_date.strftime('%Y-%m-%d'),
                str(days_remaining or 'Unknown'),
                est_end_date.strftime('%Y-%m-%d') if est_end_date else 'Unknown'
            ]

        # Define color based on media type
        if reading.media.lower() == 'audio':
            color = 'orange1'
        elif reading.media.lower() == 'hardcover':
            color = 'purple'
        elif reading.media.lower() == 'kindle':
            color = 'blue'
        else:
            color = 'white'

        return row_data, color

    def _create_table(self, title, include_progress=True):
        """Create a rich table with standard headers"""
        table = Table(
            title=title,
            show_header=True,
            header_style="bold",
            border_style="bright_black",
            pad_edge=False,
            collapse_padding=True
        )

        # Add columns with simpler styling
        table.add_column("Format", justify="center", style="white")
        table.add_column("Title", justify="left", style="white")
        table.add_column("Author", justify="left", style="white")
        table.add_column("Start Date", justify="center", style="white")
        if include_progress:
            table.add_column("Progress", justify="center", style="white")
            table.add_column("Days Elapsed", justify="center", style="white")
        table.add_column("Days to Finish", justify="center", style="white")
        table.add_column("Est. End Date", justify="center", style="white")

        return table

    def show_current_readings(self):
        """Display currently active reading sessions"""
        results = self.queries.get_current_unfinished_readings()
        table = self._create_table("Current Reading Sessions", include_progress=True)

        # Sort results by media type and title
        sorted_results = sorted(results, key=lambda x: (x.media.lower(), x.book.title))

        for reading in sorted_results:
            if reading.date_started > self.today:
                continue
            row_data, color = self._format_reading_row(reading, is_current=True)
            table.add_row(*row_data, style=color)

        console.print("\n")
        console.print(table)
        console.print("\n")

    def show_upcoming_readings(self):
        """Display upcoming reading sessions for the next 30 days"""
        results = self.queries.get_upcoming_readings()
        table = self._create_table("Upcoming Reading Sessions (Next 30 Days)", include_progress=False)

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

    def _calculate_future_progress(self, reading, target_date):
        """Calculate estimated progress for a book on a future date"""
        return calculate_reading_progress(reading, target_date)

    def show_progress_forecast(self):
        """Display daily progress forecast for the next 10 days"""
        # Get both current and upcoming readings
        current_readings = self.queries.get_current_unfinished_readings()
        upcoming_readings = self.queries.get_upcoming_readings()

        # Filter upcoming readings to only include those starting in the next 10 days
        ten_days_future = self.today + timedelta(days=10)
        upcoming_readings = [r for r in upcoming_readings
                           if r.date_est_start and r.date_est_start <= ten_days_future]

        # Combine and sort all relevant readings
        all_readings = current_readings + upcoming_readings
        all_readings.sort(key=lambda x: (x.media.lower(), x.book.title))

        if not all_readings:
            console.print("\n[yellow]No current or upcoming readings found for the next 10 days.[/yellow]\n")
            return

        # Create forecast table
        table = Table(
            title=f"10-Day Reading Progress Forecast (as of {self.today})",
            show_header=True,
            header_style="bold magenta"
        )

        # Add columns
        table.add_column("Format", justify="center")
        table.add_column("Title", justify="left")
        table.add_column("Author", justify="left")

        # Add date columns
        dates = [self.today + timedelta(days=i) for i in range(11)]  # Include today
        for d in dates:
            table.add_column(d.strftime('%m/%d'), justify="center")

        # Add rows for each reading
        for reading in all_readings:
            # Get color based on media type
            if reading.media.lower() == 'audio':
                color = 'orange1'
            elif reading.media.lower() == 'hardcover':
                color = 'purple'
            elif reading.media.lower() == 'kindle':
                color = 'blue'
            else:
                color = 'white'

            # Prepare row data
            row_data = [
                reading.media,
                reading.book.title,
                self._format_author(reading.book)
            ]

            # Add progress forecasts for each date
            for forecast_date in dates:
                progress = self._calculate_future_progress(reading, forecast_date)
                row_data.append(progress)

            table.add_row(*row_data, style=color)

        console.print("\n")
        console.print(table)
        console.print("\n")

def main():
    status = ReadingStatus()
    status.show_current_readings()
    status.show_upcoming_readings()
    status.show_progress_forecast()  # Add the new table

if __name__ == "__main__":
    main()
