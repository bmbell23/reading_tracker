"""Service for generating series statistics."""
from datetime import datetime
import csv
from pathlib import Path
from typing import List, Tuple, Any
from rich.console import Console
from rich.table import Table
from rich.style import Style
from ..models.base import engine
from sqlalchemy import text

console = Console()

class SeriesStatsService:
    """Service for generating and displaying series statistics."""

    def __init__(self):
        self.console = Console()
        # Define styles
        self.styles = {
            'header': Style(color="magenta", bold=True),
            'border': Style(color="bright_black"),
            'total': Style(color="white", bold=True),
            'highlight': Style(color="cyan"),
            'number': Style(color="green"),
            'author': Style(color="yellow"),
            'title': Style(color="blue", bold=True),
        }

    def _get_queries(self, finished_only: bool) -> dict[str, str]:
        """Get the SQL queries for series statistics."""
        finished_condition = "AND r.date_finished_actual IS NOT NULL" if finished_only else ""
        
        return {
            'series': f"""
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as book_count,
                    SUM(b.word_count) as total_words,
                    GROUP_CONCAT(DISTINCT b.author_name_first || ' ' || b.author_name_second) as author
                FROM books b
                INNER JOIN read r ON b.id = r.book_id
                WHERE b.series IS NOT NULL {finished_condition}
                GROUP BY b.series
                ORDER BY total_words DESC
            """,
            'standalone': f"""
                SELECT
                    b.title,
                    b.author_name_first || ' ' || b.author_name_second as author,
                    b.word_count
                FROM books b
                INNER JOIN read r ON b.id = r.book_id
                WHERE b.series IS NULL {finished_condition}
                ORDER BY b.word_count DESC
            """,
            'reread': f"""
                SELECT
                    b.title,
                    b.author_name_first || ' ' || b.author_name_second as author,
                    COUNT(*) as times_read,
                    b.word_count,
                    (COUNT(*) * b.word_count) - b.word_count as additional_words
                FROM books b
                INNER JOIN read r ON b.id = r.book_id
                {f"WHERE r.date_finished_actual IS NOT NULL" if finished_only else ""}
                GROUP BY b.id, b.title, b.author_name_first, b.author_name_second, b.word_count
                HAVING COUNT(*) > 1
                ORDER BY additional_words DESC
            """
        }

    def _format_number(self, number: int) -> str:
        """Format a number with commas and color."""
        return f"[green]{number:,}[/green]"

    def _create_series_table(self, results: List[Tuple]) -> Table:
        """Create a table for series statistics."""
        table = Table(
            title="📚 Series Statistics",
            show_header=True,
            header_style=self.styles['header'],
            border_style=self.styles['border'],
            title_style=self.styles['title'],
            pad_edge=False,
            collapse_padding=True
        )

        table.add_column("Series Name", justify="left", style="cyan")
        table.add_column("Author(s)", justify="left", style="yellow")
        table.add_column("Books", justify="right", style="green")
        table.add_column("Total Words", justify="right", style="green")
        table.add_column("Avg Words/Book", justify="right", style="green")

        total_books = 0
        total_words = 0

        for row in results:
            series = row[0] or "[dim]N/A[/dim]"
            authors = row[3] or "[dim]Unknown[/dim]"
            books = row[1]
            words = row[2] or 0
            avg_words = int(words / books) if books else 0

            total_books += books
            total_words += words

            table.add_row(
                series,
                authors,
                str(books),
                f"{words:,}",
                f"{avg_words:,}"
            )

        # Add total row
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            "",
            f"[bold green]{total_books:,}[/bold green]",
            f"[bold green]{total_words:,}[/bold green]",
            f"[bold green]{int(total_words/total_books):,}[/bold green]" if total_books else "0",
            style="bold white"
        )

        return table

    def _create_standalone_table(self, results: List[Tuple]) -> Table:
        """Create a table for standalone book statistics."""
        table = Table(
            title="📖 Standalone Books",
            show_header=True,
            header_style=self.styles['header'],
            border_style=self.styles['border'],
            title_style=self.styles['title'],
            pad_edge=False,
            collapse_padding=True
        )

        table.add_column("Title", justify="left", style="cyan")
        table.add_column("Author", justify="left", style="yellow")
        table.add_column("Words", justify="right", style="green")

        total_words = 0

        for row in results:
            title = row[0] or "[dim]N/A[/dim]"
            author = row[1] or "[dim]Unknown[/dim]"
            words = row[2] or 0
            total_words += words

            table.add_row(
                title,
                author,
                f"{words:,}"
            )

        # Add total row
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            "",
            f"[bold green]{total_words:,}[/bold green]",
            style="bold white"
        )

        return table

    def _create_reread_table(self, results: List[Tuple]) -> Table:
        """Create a table for reread statistics."""
        table = Table(
            title="🔄 Reread Books",
            show_header=True,
            header_style=self.styles['header'],
            border_style=self.styles['border'],
            title_style=self.styles['title'],
            pad_edge=False,
            collapse_padding=True
        )

        table.add_column("Title", justify="left", style="cyan")
        table.add_column("Author", justify="left", style="yellow")
        table.add_column("Times Read", justify="right", style="green")
        table.add_column("Base Words", justify="right", style="green")
        table.add_column("Additional Words", justify="right", style="green")

        total_rereads = 0
        total_base_words = 0
        total_additional_words = 0

        for row in results:
            title = row[0] or "[dim]N/A[/dim]"
            author = row[1] or "[dim]Unknown[/dim]"
            times_read = row[2]
            base_words = row[3] or 0
            additional_words = row[4] or 0

            total_rereads += times_read - 1  # Subtract first read
            total_base_words += base_words
            total_additional_words += additional_words

            table.add_row(
                title,
                author,
                str(times_read),
                f"{base_words:,}",
                f"{additional_words:,}"
            )

        # Add total row
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            "",
            f"[bold green]{total_rereads:,}[/bold green]",
            f"[bold green]{total_base_words:,}[/bold green]",
            f"[bold green]{total_additional_words:,}[/bold green]",
            style="bold white"
        )

        return table

    def _create_summary_table(self, data: dict) -> Table:
        """Create a summary table with overall statistics."""
        table = Table(
            title="📊 Overall Reading Statistics",
            show_header=True,
            header_style=self.styles['header'],
            border_style=self.styles['border'],
            title_style=self.styles['title'],
            pad_edge=False,
            collapse_padding=True
        )

        table.add_column("Category", justify="left", style="cyan")
        table.add_column("Books", justify="right", style="green")
        table.add_column("Words", justify="right", style="green")
        table.add_column("Percentage", justify="right", style="yellow")

        # Calculate totals
        series_books = sum(row[1] for row in data['series'])
        series_words = sum(row[2] or 0 for row in data['series'])
        
        standalone_books = len(data['standalone'])
        standalone_words = sum(row[2] or 0 for row in data['standalone'])
        
        reread_books = sum(row[2] - 1 for row in data['reread'])  # Subtract first read
        reread_words = sum(row[4] or 0 for row in data['reread'])

        total_books = series_books + standalone_books + reread_books
        total_words = series_words + standalone_words + reread_words

        # Add rows
        for category, books, words in [
            ("Series", series_books, series_words),
            ("Standalone", standalone_books, standalone_words),
            ("Reread", reread_books, reread_words)
        ]:
            percentage = (words / total_words * 100) if total_words > 0 else 0
            table.add_row(
                category,
                f"{books:,}",
                f"{words:,}",
                f"{percentage:.1f}%"
            )

        # Add total row
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            f"[bold green]{total_books:,}[/bold green]",
            f"[bold green]{total_words:,}[/bold green]",
            "[bold yellow]100.0%[/bold yellow]",
            style="bold white"
        )

        return table

    def _save_to_csv(self, data: dict, finished_only: bool) -> Path:
        """Save statistics to CSV files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        status = "finished" if finished_only else "all"
        
        csv_dir = Path("csv") / f"series_stats_{status}_{timestamp}"
        csv_dir.mkdir(parents=True, exist_ok=True)

        # Save series data
        series_path = csv_dir / "series.csv"
        with open(series_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Series Name', 'Author(s)', 'Book Count', 'Total Words'])
            for row in data['series']:
                writer.writerow([
                    row[0] or "N/A",
                    row[3] or "Unknown",
                    row[1],
                    row[2] or 0
                ])

        # Save standalone data
        standalone_path = csv_dir / "standalone.csv"
        with open(standalone_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Author', 'Word Count'])
            for row in data['standalone']:
                writer.writerow([
                    row[0] or "N/A",
                    row[1] or "Unknown",
                    row[2] or 0
                ])

        # Save reread data
        reread_path = csv_dir / "rereads.csv"
        with open(reread_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Author', 'Times Read', 'Base Words', 'Additional Words'])
            for row in data['reread']:
                writer.writerow([
                    row[0] or "N/A",
                    row[1] or "Unknown",
                    row[2],
                    row[3] or 0,
                    row[4] or 0
                ])

        return csv_dir

    def generate_stats(self, finished_only: bool = False, csv_output: bool = False) -> None:
        """
        Generate and display series statistics.

        Args:
            finished_only: If True, only include finished books
            csv_output: If True, also save results to CSV
        """
        with engine.connect() as conn:
            queries = self._get_queries(finished_only)
            results = {
                name: conn.execute(text(query)).fetchall()
                for name, query in queries.items()
            }

            if csv_output:
                output_dir = self._save_to_csv(results, finished_only)
                console.print(f"\n[blue]CSV files have been created in:[/blue] {output_dir}")

            # Display tables with spacing
            console.print("\n")
            console.print(self._create_series_table(results['series']))
            console.print("\n")
            console.print(self._create_standalone_table(results['standalone']))
            console.print("\n")
            console.print(self._create_reread_table(results['reread']))
            console.print("\n")
            console.print(self._create_summary_table(results))
            console.print("\n")
