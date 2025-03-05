"""Service for displaying reading status information."""
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from ..models.reading_status import ReadingStatus as ModelReadingStatus
from ..utils.progress_calculator import calculate_reading_progress

console = Console()

class StatusDisplay:
    """Service for managing and displaying reading status information."""

    def __init__(self):
        self.model = ModelReadingStatus()
        self.today = date.today()

    def _format_author(self, book):
        """Format author name from book object."""
        return f"{book.author_name_first or ''} {book.author_name_second or ''}".strip()

    def _create_table(self, title, include_progress=True):
        """Create a rich table with standard headers."""
        table = Table(
            title=title,
            show_header=True,
            header_style="bold",
            border_style="bright_black",
            pad_edge=False,
            collapse_padding=True
        )

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

    def _get_row_color(self, media):
        """Get color based on media type."""
        media_lower = media.lower()
        if media_lower == 'audio':
            return 'orange1'
        elif media_lower == 'hardcover':
            return 'purple'
        elif media_lower == 'kindle':
            return 'blue'
        return 'white'

    def _format_media_badge(self, media: str) -> str:
        """Format media type as an HTML badge."""
        media_colors = {
            'kindle': ('#EFF6FF', '#3B82F6'),    # Light blue bg, blue text
            'ebook': ('#EFF6FF', '#3B82F6'),     # Light blue bg, blue text
            'hardcover': ('#FAF5FF', '#A855F7'), # Light purple bg, purple text
            'audio': ('#FFF7ED', '#FB923C'),     # Light orange bg, orange text
            'audiobook': ('#FFF7ED', '#FB923C'), # Light orange bg, orange text
        }

        bg_color, text_color = media_colors.get(media.lower(), ('#F3F4F6', '#4B5563'))  # Default: light gray bg, gray text

        return f"""<span style="
            background-color: {bg_color};
            color: {text_color};
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            text-transform: capitalize;
        ">{media}</span>"""

    def show_current_readings(self):
        """Display currently active reading sessions."""
        results = self.model.get_current_readings()
        table = self._create_table("Current Reading Sessions", include_progress=True)

        sorted_results = sorted(results, key=lambda x: (x.media.lower(), x.book.title))

        for reading in sorted_results:
            if reading.date_started > self.today:
                continue

            days_elapsed = (self.today - reading.date_started).days if reading.date_started else 0
            progress = calculate_reading_progress(reading, self.today)

            # Calculate remaining days using date_est_end
            days_remaining = None
            if reading.date_est_end:
                days_remaining = (reading.date_est_end - self.today).days
                if days_remaining < 0:
                    days_remaining = 0

            row_data = [
                reading.media,
                reading.book.title,
                self._format_author(reading.book),
                reading.date_started.strftime('%Y-%m-%d') if reading.date_started else 'Not started',
                progress,
                str(days_elapsed),
                str(days_remaining if days_remaining is not None else 'Unknown'),
                reading.date_est_end.strftime('%Y-%m-%d') if reading.date_est_end else 'Unknown'
            ]

            table.add_row(*row_data, style=self._get_row_color(reading.media))

        console.print("\n")
        console.print(table)
        console.print("\n")

    def show_upcoming_readings(self):
        """Display upcoming reading sessions for the next 30 days."""
        results = self.model.get_upcoming_readings()
        table = self._create_table("Upcoming Reading Sessions (Next 30 Days)", include_progress=False)

        sorted_results = sorted(results, key=lambda x: x.date_est_start or date.max)

        for reading in sorted_results:
            if not reading.date_est_start:
                continue

            row_data = [
                reading.media,
                reading.book.title,
                self._format_author(reading.book),
                reading.date_est_start.strftime('%Y-%m-%d') if reading.date_est_start else 'Not scheduled',
                str(reading.days_estimate if reading.days_estimate else 'Unknown'),
                reading.date_est_end.strftime('%Y-%m-%d') if reading.date_est_end else 'Unknown'
            ]

            table.add_row(*row_data, style=self._get_row_color(reading.media))

        console.print("\n")
        if sorted_results:
            console.print(table)
        else:
            console.print("[yellow]No upcoming reading sessions found for the next 30 days.[/yellow]")
        console.print("\n")

    def _format_forecast_progress(self, reading, forecast_date):
        """Format progress specifically for forecast display."""
        # For books not yet started
        start_date = reading.date_started or reading.date_est_start
        if not start_date or forecast_date < start_date:
            return "TBR"

        # For completed books
        if reading.date_est_end and forecast_date > reading.date_est_end:
            return "Done"

        # For books on their start date or after
        if forecast_date >= start_date:
            total_days = (reading.date_est_end - start_date).days + 1
            days_elapsed = (forecast_date - start_date).days + 1
            if total_days > 0:
                progress = (days_elapsed / total_days) * 100
                return f"{int(round(progress))}%"

        return "0%"

    def show_progress_forecast(self):
        """Display daily progress forecast for the next 7 days."""
        all_readings = self.model.get_forecast_readings()

        if not all_readings:
            console.print("\n[yellow]No current or upcoming readings found for the next 7 days.[/yellow]\n")
            return

        table = Table(
            title=f"Weekly Reading Progress Forecast (as of {self.today})",
            show_header=True,
            header_style="bold magenta"
        )

        table.add_column("Format", justify="center")
        table.add_column("Title", justify="left")
        table.add_column("Author", justify="left")

        dates = [self.today + timedelta(days=i) for i in range(8)]
        for d in dates:
            day_name = d.strftime('%a')
            date_str = d.strftime('%m/%d')
            table.add_column(f"{day_name}\n{date_str}", justify="center")

        for reading in all_readings:
            row_data = [
                reading.media,
                reading.book.title,
                self._format_author(reading.book)
            ]

            for forecast_date in dates:
                progress = self._format_forecast_progress(reading, forecast_date)
                row_data.append(progress)

            table.add_row(*row_data, style=self._get_row_color(reading.media))

        console.print("\n")
        console.print(table)
        console.print("\n")
