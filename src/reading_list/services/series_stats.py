"""Service for generating series statistics."""
from datetime import datetime
import csv
from pathlib import Path
from typing import List, Tuple, Any
from rich.console import Console
from rich.table import Table
from rich.style import Style
from sqlalchemy import text, func
from ..models.base import engine
from ..queries.common_queries import CommonQueries

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

    def _get_queries(self, finished_only: bool = False, upcoming: bool = False) -> dict[str, str]:
        """Get SQL queries for statistics."""
        base_condition = """
            r.date_finished_actual IS NOT NULL
        """ if not upcoming else """
            r.date_est_start IS NOT NULL
            AND r.date_est_end IS NOT NULL
            AND r.date_finished_actual IS NULL
        """

        if finished_only and not upcoming:
            base_condition += " AND r.date_finished_actual IS NOT NULL"

        return {
            "series": f"""
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as book_count,
                    SUM(DISTINCT b.word_count) as total_words,
                    GROUP_CONCAT(DISTINCT COALESCE(b.author_name_first || ' ' || b.author_name_second, '')) as authors
                FROM books b
                JOIN read r ON r.book_id = b.id
                WHERE b.series IS NOT NULL
                AND {base_condition}
                GROUP BY b.series
                ORDER BY total_words DESC
            """,
            "series_total": """
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as total_book_count
                FROM books b
                WHERE b.series IS NOT NULL
                GROUP BY b.series
            """,
            "future_books": """
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as future_book_count
                FROM books b
                LEFT JOIN read r ON b.id = r.book_id AND r.date_finished_actual IS NOT NULL
                WHERE b.series IS NOT NULL
                AND r.id IS NULL  -- Only include books that haven't been read
                AND (b.date_published IS NULL OR b.date_published > DATE('now'))
                GROUP BY b.series
            """,
            "standalone": f"""
                SELECT
                    b.title,
                    COALESCE(b.author_name_first || ' ' || b.author_name_second, '') as author,
                    b.word_count
                FROM books b
                JOIN read r ON r.book_id = b.id
                WHERE b.series IS NULL
                AND {base_condition}
                GROUP BY b.id
                ORDER BY b.word_count DESC
            """
        }

    def _format_number(self, number: int) -> str:
        """Format a number with commas and color."""
        return f"[green]{number:,}[/green]"

    def _create_series_table(self, results: List[Tuple], total_counts: List[Tuple], future_counts: List[Tuple]) -> Table:
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
        table.add_column("Read", justify="right", style="green")
        table.add_column("Unread", justify="right", style="red")
        table.add_column("Total", justify="right", style="blue")
        table.add_column("Total Words", justify="right", style="green")
        table.add_column("Avg Words/Book", justify="right", style="green")

        total_read_books = 0
        total_unread_books = 0
        total_all_books = 0
        total_words = 0

        # Create a dictionary of total book counts by series
        total_counts_dict = {row[0]: row[1] for row in total_counts}

        # Create a dictionary of future/unpublished book counts by series
        future_counts_dict = {row[0]: row[1] for row in future_counts}

        for row in results:
            series = row[0] or "[dim]N/A[/dim]"
            authors = row[3] or "[dim]Unknown[/dim]"
            read_books = row[1]
            words = row[2] or 0
            # If we have a total count for this series, use it; otherwise, use read_books as the total
            total_books = max(read_books, total_counts_dict.get(series, read_books))

            # Get the number of future/unpublished books in this series
            future_books = future_counts_dict.get(series, 0)

            # Calculate unread books, excluding future/unpublished books
            # We don't want to count future/unpublished books as "unread"
            unread_books = max(0, total_books - read_books - future_books)

            avg_words = int(words / read_books) if read_books else 0

            total_read_books += read_books
            total_unread_books += unread_books
            total_all_books += total_books
            total_words += words

            table.add_row(
                series,
                authors,
                str(read_books),
                "" if unread_books == 0 else str(unread_books),  # Show blank instead of 0
                str(total_books),
                f"{words:,}",
                f"{avg_words:,}"
            )

        # Add total row
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            "",
            f"[bold green]{total_read_books:,}[/bold green]",
            f"[bold red]{total_unread_books:,}[/bold red]" if total_unread_books > 0 else "",
            f"[bold blue]{total_all_books:,}[/bold blue]",
            f"[bold green]{total_words:,}[/bold green]",
            f"[bold green]{int(total_words/total_read_books):,}[/bold green]" if total_read_books else "0",
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

        # Create a dictionary of total book counts by series
        total_counts_dict = {row[0]: row[1] for row in data['series_total']}

        # Create a dictionary of future/unpublished book counts by series
        future_counts_dict = {row[0]: row[1] for row in data['future_books']}

        # Save series data
        series_path = csv_dir / "series.csv"
        with open(series_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Series Name', 'Author(s)', 'Read Books', 'Unread Books', 'Future Books', 'Total Books', 'Total Words'])
            for row in data['series']:
                series = row[0] or "N/A"
                read_books = row[1]
                # If we have a total count for this series, use it; otherwise, use read_books as the total
                total_books = max(read_books, total_counts_dict.get(series, read_books))
                # Get the number of future/unpublished books in this series
                future_books = future_counts_dict.get(series, 0)
                # Calculate unread books, excluding future/unpublished books
                unread_books = max(0, total_books - read_books - future_books)

                writer.writerow([
                    series,
                    row[3] or "Unknown",
                    read_books,
                    "" if unread_books == 0 else unread_books,  # Show blank instead of 0
                    future_books,
                    total_books,
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

    def generate_stats(self, finished_only: bool = False, csv_output: bool = False, upcoming: bool = False) -> None:
        """
        Generate and display series statistics.

        Args:
            finished_only: If True, only include finished books
            csv_output: If True, also save results to CSV
            upcoming: If True, show upcoming books instead of finished books
        """
        with engine.connect() as conn:
            queries = self._get_queries(finished_only, upcoming)
            results = {
                name: conn.execute(text(query)).fetchall()
                for name, query in queries.items()
            }

            # Get reread data using common query
            common_queries = CommonQueries()
            reread_results = common_queries.get_reread_books(
                reread_type='upcoming' if upcoming else 'finished'
            )

            # Transform reread results to match expected format
            if upcoming:
                results['reread'] = [
                    (
                        reading.book.title,
                        f"{reading.book.author_name_first} {reading.book.author_name_second}".strip(),
                        2,  # For upcoming, it's always 2 (1 previous + 1 upcoming)
                        reading.book.word_count,
                        reading.book.word_count  # For upcoming, additional words is just the word count once
                    )
                    for reading in reread_results
                ]
            else:
                results['reread'] = [
                    (
                        reading[0].book.title,
                        f"{reading[0].book.author_name_first} {reading[0].book.author_name_second}".strip(),
                        reading[1],
                        reading[0].book.word_count,
                        reading[0].book.word_count * (reading[1] - 1)  # Additional words from rereads
                    )
                    for reading in reread_results
                ]

            if csv_output:
                output_dir = self._save_to_csv(results, finished_only)
                console.print(f"\n[blue]CSV files have been created in:[/blue] {output_dir}")

            # Display tables with spacing
            console.print("\n")
            console.print(self._create_series_table(results['series'], results['series_total'], results['future_books']))
            console.print("\n")
            console.print(self._create_standalone_table(results['standalone']))
            console.print("\n")
            console.print(self._create_reread_table(results['reread']))
            console.print("\n")
            console.print(self._create_summary_table(results))
            console.print("\n")
