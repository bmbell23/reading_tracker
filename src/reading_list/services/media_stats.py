"""Service for generating media statistics."""
from datetime import datetime
import csv
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from ..models.base import engine
from sqlalchemy import text

console = Console()

class MediaStatsService:
    """Service for generating and displaying media statistics."""
    
    def __init__(self):
        self.console = Console()

    def _get_stats_query(self, finished_only: bool) -> str:
        """Get the SQL query for media statistics."""
        base_query = """
            SELECT
                r.media,
                COUNT(DISTINCT r.book_id) as book_count,
                SUM(b.word_count) as total_words
            FROM read r
            INNER JOIN books b ON r.book_id = b.id
            {where_clause}
            GROUP BY r.media
            ORDER BY book_count DESC
        """
        where_clause = "WHERE r.date_finished_actual IS NOT NULL" if finished_only else ""
        return base_query.format(where_clause=where_clause)

    def _get_media_color(self, media: str) -> str:
        """Get the display color for a media type."""
        media_colors = {
            'audio': 'orange1',
            'hardcover': 'purple',
            'kindle': 'blue'
        }
        return media_colors.get(media.lower(), 'white')

    def _create_stats_table(self, results, total_books, total_words, finished_only: bool) -> Table:
        """Create a rich table for displaying media statistics."""
        status = "Finished" if finished_only else "All"
        table = Table(title=f"Reading Statistics by Media ({status} Books)")

        table.add_column("Media", justify="left")
        table.add_column("Books", justify="right")
        table.add_column("Words", justify="right")
        table.add_column("Books %", justify="right")
        table.add_column("Words %", justify="right")

        for row in results:
            media = row[0] or "Unknown"
            books = row[1]
            words = row[2] or 0
            books_percent = (books / total_books * 100) if total_books else 0
            words_percent = (words / total_words * 100) if total_words else 0

            table.add_row(
                media,
                str(books),
                f"{words:,}",
                f"{books_percent:.1f}%",
                f"{words_percent:.1f}%",
                style=self._get_media_color(media)
            )

        table.add_row(
            "Total",
            str(total_books),
            f"{total_words:,}",
            "100.0%",
            "100.0%",
            style="bold white"
        )

        return table

    def _save_to_csv(self, results, total_books, total_words, finished_only: bool) -> Path:
        """Save statistics to a CSV file."""
        csv_dir = Path("csv")
        csv_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        status = "finished" if finished_only else "all"
        filename = f"media_stats_{status}_{timestamp}.csv"
        filepath = csv_dir / filename

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Media', 'Books', 'Words', 'Books %', 'Words %'])
            for row in results:
                media = row[0] or "Unknown"
                books = row[1]
                words = row[2] or 0
                books_percent = (books / total_books * 100) if total_books else 0
                words_percent = (words / total_words * 100) if total_words else 0
                writer.writerow([
                    media,
                    books,
                    words,
                    f"{books_percent:.1f}%",
                    f"{words_percent:.1f}%"
                ])

        return filepath

    def generate_stats(self, finished_only: bool = False, csv_output: bool = False) -> None:
        """
        Generate and display media statistics.

        Args:
            finished_only: If True, only include finished books
            csv_output: If True, also save results to CSV
        """
        with engine.connect() as conn:
            query = self._get_stats_query(finished_only)
            results = conn.execute(text(query)).fetchall()

            total_books = sum(row[1] for row in results)
            total_words = sum(row[2] or 0 for row in results)

            if csv_output:
                filepath = self._save_to_csv(results, total_books, total_words, finished_only)
                console.print(f"\nCSV file has been created: {filepath}")

            table = self._create_stats_table(results, total_books, total_words, finished_only)
            console.print("\n")
            console.print(table)
            console.print("\n")