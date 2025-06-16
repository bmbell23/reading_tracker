"""Service for generating series statistics."""
from datetime import datetime
import csv
from pathlib import Path
from typing import List, Tuple
from rich.console import Console
from rich.table import Table, Column
from rich.style import Style
from rich.box import SIMPLE_HEAD
from sqlalchemy import text
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
            'author': Style(color="blue"),
            'title': Style(color="blue", bold=True),
        }

    def _get_queries(self, finished_only: bool = False, upcoming: bool = False) -> dict[str, str]:
        """Get SQL queries for statistics."""
        if upcoming:
            base_condition = "r.date_finished_actual IS NULL AND r.date_est_start IS NOT NULL AND r.date_est_end IS NOT NULL"
        elif finished_only:
            base_condition = "r.date_finished_actual IS NOT NULL"
        else:
            base_condition = "1=1"  # Always true

        return {
            "series": f"""
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as book_count,
                    SUM(DISTINCT b.word_count) as total_words,
                    (SELECT GROUP_CONCAT(DISTINCT author) FROM (
                        SELECT DISTINCT
                            CASE
                                WHEN b2.author_name_first = 'Sue' AND b2.author_name_second = 'Lynn Tan'
                                THEN 'Sue Lynn Tan'
                                WHEN b2.author_name_first = 'Evan' AND (b2.author_name_second = 'Winter' OR b2.author_name_second = 'Winters')
                                THEN 'Evan Winter'
                                WHEN b2.author_name_first = 'VE' OR b2.author_name_first = 'Ve'
                                THEN 'VE Schwab'
                                ELSE COALESCE(b2.author_name_first || ' ' || b2.author_name_second, '')
                            END as author
                        FROM books b2
                        WHERE b2.series = b.series
                        GROUP BY
                            CASE
                                WHEN LOWER(b2.author_name_first) IN ('sue', 've', 'evan')
                                THEN LOWER(b2.author_name_first)
                                ELSE LOWER(TRIM(COALESCE(b2.author_name_first, '') || ' ' || COALESCE(b2.author_name_second, '')))
                            END
                    )) as authors,
                    SUM(CASE
                        WHEN b.word_count >= 45000
                        THEN 1
                        ELSE 0
                    END) as novel_count,
                    SUM(CASE
                        WHEN b.word_count < 45000
                        THEN 1
                        ELSE 0
                    END) as novella_count
                FROM books b
                JOIN read r ON r.book_id = b.id
                WHERE b.series IS NOT NULL
                AND {base_condition}
                AND (r.reread IS NULL OR r.reread = 0)
                GROUP BY b.series
                ORDER BY total_words DESC
            """,
            "series_total": """
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as total_book_count,
                    SUM(CASE
                        WHEN b.word_count >= 45000
                        THEN 1
                        ELSE 0
                    END) as total_novel_count,
                    SUM(CASE
                        WHEN b.word_count < 45000
                        THEN 1
                        ELSE 0
                    END) as total_novella_count,
                    (SELECT COUNT(*) FROM read r WHERE r.book_id IN (SELECT id FROM books WHERE series = b.series) AND r.date_finished_actual IS NOT NULL) as read_count
                FROM books b
                WHERE b.series IS NOT NULL
                GROUP BY b.series
            """,
            "future_books": """
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as future_book_count,
                    SUM(CASE
                        WHEN b.word_count >= 45000
                        THEN 1
                        ELSE 0
                    END) as future_novel_count,
                    SUM(CASE
                        WHEN b.word_count < 45000
                        THEN 1
                        ELSE 0
                    END) as future_novella_count,
                    SUM(b.word_count) as future_words
                FROM books b
                LEFT JOIN read r ON b.id = r.book_id AND r.date_finished_actual IS NOT NULL
                WHERE b.series IS NOT NULL
                AND r.id IS NULL  -- Only include books that haven't been read
                AND (b.date_published IS NULL OR b.date_published > DATE('now'))
                GROUP BY b.series
            """,
            "unread_books": """
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as unread_book_count,
                    SUM(CASE
                        WHEN b.word_count >= 45000
                        THEN 1
                        ELSE 0
                    END) as unread_novel_count,
                    SUM(CASE
                        WHEN b.word_count < 45000
                        THEN 1
                        ELSE 0
                    END) as unread_novella_count,
                    SUM(b.word_count) as unread_words
                FROM books b
                LEFT JOIN read r ON b.id = r.book_id AND r.date_finished_actual IS NOT NULL
                WHERE b.series IS NOT NULL
                AND r.id IS NULL  -- Only include books that haven't been read
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
                AND (r.reread IS NULL OR r.reread = 0)
                GROUP BY b.id
                ORDER BY b.word_count DESC
            """
        }

    def _format_number(self, number: int) -> str:
        """Format a number with commas and color."""
        return f"[green]{number:,}[/green]"

    def _create_series_table(self, results: List[Tuple], total_counts: List[Tuple], future_counts: List[Tuple], unread_counts: List[Tuple]) -> Table:
        """Create a table for series statistics."""
        # Create a table with two header rows
        table = Table(
            title="📚 Series Statistics",
            show_header=True,
            header_style=self.styles['header'],
            border_style=self.styles['border'],
            title_style=self.styles['title'],
            pad_edge=False,
            collapse_padding=True,
            box=SIMPLE_HEAD
        )

        # Add columns with empty headers (we'll add the actual headers in the first row)
        table.add_column(header="", justify="left", style="cyan", no_wrap=True)  # Series Name
        table.add_column(header="", justify="left", style="blue")  # Author(s)

        # Novels columns
        table.add_column(header="", justify="right", style="green")  # Read
        table.add_column(header="", justify="right", style="red")    # Unread
        table.add_column(header="", justify="right", style="blue")   # Total

        # Novellas columns
        table.add_column(header="", justify="right", style="green")  # Read
        table.add_column(header="", justify="right", style="red")    # Unread
        table.add_column(header="", justify="right", style="blue")   # Total

        # Words columns
        table.add_column(header="", justify="right", style="green")  # Read Words
        table.add_column(header="", justify="right", style="red")    # Unread Words
        table.add_column(header="", justify="right", style="blue")   # Total Words

        # Add the first header row with column groups
        table.add_row(
            "Series Name",
            "Author(s)",
            "", "[bold magenta]Novels[/bold magenta]", "",
            "", "[bold magenta]Novellas[/bold magenta]", "",
            "Read Words",
            "Unread Words",
            "Total Words"
        )

        # Add the second header row with column names
        table.add_row(
            "",
            "",
            "[bold green]Read[/bold green]",
            "[bold red]Unread[/bold red]",
            "[bold blue]Total[/bold blue]",
            "[bold green]Read[/bold green]",
            "[bold red]Unread[/bold red]",
            "[bold blue]Total[/bold blue]",
            "",
            "",
            ""
        )

        total_read_books = 0
        total_unread_books = 0
        total_all_books = 0
        total_read_words = 0
        total_unread_words = 0

        # We'll use direct lookups with next() instead of dictionaries

        for row in results:
            series_name = row[0] or "N/A"
            authors = row[3] or "[dim]Unknown[/dim]"
            read_books = row[1]
            read_words = row[2] or 0
            read_novels = row[4] or 0
            read_novellas = row[5] or 0

            # Get total counts for this series
            total_count_row = next((r for r in total_counts if r[0] == series_name), None)
            total_books = total_count_row[1] if total_count_row else read_books
            total_novels = total_count_row[2] if total_count_row else read_novels
            total_novellas = total_count_row[3] if total_count_row else read_novellas

            # Get the number of future/unpublished books in this series
            future_count_row = next((r for r in future_counts if r[0] == series_name), None)
            future_books = future_count_row[1] if future_count_row else 0
            future_novels = future_count_row[2] if future_count_row else 0
            future_novellas = future_count_row[3] if future_count_row else 0

            # Get the unread books for this series
            unread_count_row = next((r for r in unread_counts if r[0] == series_name), None)
            unread_words = unread_count_row[4] if unread_count_row and len(unread_count_row) > 4 else 0

            # Calculate unread books, excluding future/unpublished books
            # We don't want to count future/unpublished books as "unread"
            unread_books = max(0, total_books - read_books - future_books)
            unread_novels = max(0, total_novels - read_novels - future_novels)
            unread_novellas = max(0, total_novellas - read_novellas - future_novellas)

            total_read_books += read_books
            total_unread_books += unread_books
            total_all_books += total_books
            total_read_words += read_words
            total_unread_words += unread_words

            # Get the read count for this series
            total_count_row = next((r for r in total_counts if r[0] == series_name), None)
            read_count = total_count_row[4] if total_count_row and len(total_count_row) > 4 else 0

            # Color-code the series name based on status:
            # - Gray for series that haven't been started (no books read)
            # - Red for series with unread novels
            # - Orange for series with unread novellas (but no unread novels)
            # - Yellow for series with only unpublished books
            # - Green for completed series
            if read_count == 0:
                # Series hasn't been started - make it gray
                series = f"[dim white]{series_name}[/dim white]"
            elif unread_novels > 0:
                # Series has unread novels - make it red
                series = f"[bold red]{series_name}[/bold red]"
            elif unread_novellas > 0:
                # Series has unread novellas but no unread novels - make it orange
                series = f"[bold orange3]{series_name}[/bold orange3]"
            elif future_books > 0:
                # Series has only unpublished books - make it yellow
                series = f"[bold yellow]{series_name}[/bold yellow]"
            else:
                # Series is complete - make it green
                series = f"[bold green]{series_name}[/bold green]"

            # Calculate total words for this series
            total_series_words = read_words + unread_words

            table.add_row(
                series,
                authors,
                str(read_novels),
                "" if unread_novels == 0 else str(unread_novels),  # Show blank instead of 0
                str(total_novels),
                str(read_novellas),
                "" if unread_novellas == 0 else str(unread_novellas),  # Show blank instead of 0
                str(total_novellas),
                f"{read_words:,}",
                f"{unread_words:,}" if unread_words > 0 else "",  # Show blank instead of 0
                f"{total_series_words:,}"
            )

        # Calculate totals for novels and novellas
        total_read_novels = sum(row[4] or 0 for row in results)
        total_read_novellas = sum(row[5] or 0 for row in results)

        # Calculate total unread novels and novellas
        total_unread_novels = 0
        total_unread_novellas = 0
        total_novels = 0
        total_novellas = 0

        for series_name in {row[0] for row in results}:
            # Get total counts for this series
            total_count_row = next((r for r in total_counts if r[0] == series_name), None)
            if total_count_row:
                total_novels += total_count_row[2] or 0
                total_novellas += total_count_row[3] or 0

            # Get future counts for this series
            future_count_row = next((r for r in future_counts if r[0] == series_name), None)
            future_novels = future_count_row[2] if future_count_row else 0
            future_novellas = future_count_row[3] if future_count_row else 0

            # Get read counts for this series
            read_row = next((r for r in results if r[0] == series_name), None)
            read_novels = read_row[4] if read_row else 0
            read_novellas = read_row[5] if read_row else 0

            # Calculate unread counts
            unread_novels = max(0, (total_count_row[2] or 0) - read_novels - future_novels)
            unread_novellas = max(0, (total_count_row[3] or 0) - read_novellas - future_novellas)

            total_unread_novels += unread_novels
            total_unread_novellas += unread_novellas

        # Calculate total words (read + unread)
        total_words = total_read_words + total_unread_words

        # Add total row with bold styling
        table.add_row(
            "[bold white]TOTAL[/bold white]",
            "",
            f"[bold green]{total_read_novels:,}[/bold green]",
            f"[bold red]{total_unread_novels:,}[/bold red]" if total_unread_novels > 0 else "",
            f"[bold blue]{total_novels:,}[/bold blue]",
            f"[bold green]{total_read_novellas:,}[/bold green]",
            f"[bold red]{total_unread_novellas:,}[/bold red]" if total_unread_novellas > 0 else "",
            f"[bold blue]{total_novellas:,}[/bold blue]",
            f"[bold green]{total_read_words:,}[/bold green]",
            f"[bold red]{total_unread_words:,}[/bold red]" if total_unread_words > 0 else "",
            f"[bold blue]{total_words:,}[/bold blue]",
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
        table.add_column("Author", justify="left", style="blue")
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
            title="🔄 Books Read Multiple Times",
            caption=(
                "Individual rows show total reads per book, total row shows additional reads only "
                "(matching 'Additional Reads' in summary)"
            ),
            show_header=True,
            header_style=self.styles['header'],
            border_style=self.styles['border'],
            title_style=self.styles['title'],
            pad_edge=False,
            collapse_padding=True
        )

        table.add_column("Title", justify="left", style="cyan")
        table.add_column("Author", justify="left", style="blue")
        table.add_column("Times Read (Total)", justify="right", style="green")
        table.add_column("Base Words", justify="right", style="green")
        table.add_column("Additional Words", justify="right", style="green")

        # For the reread table rows, we show the total times each book was read (including first read)
        # But for the total row and summary table, we only count the additional reads beyond the first
        # This is because the first read is already counted in either Series or Standalone
        total_rereads = 0
        total_base_words = 0
        total_additional_words = 0

        for row in results:
            title = row[0] or "[dim]N/A[/dim]"
            author = row[1] or "[dim]Unknown[/dim]"
            times_read = row[2]
            base_words = row[3] or 0
            additional_words = row[4] or 0

            # For individual rows, we show total times read
            # But for the total row, we'll show additional reads to match the summary table
            total_rereads += times_read - 1  # Count additional reads for the total
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
            # Show only additional reads in total (matches summary table)
            f"[bold green]{total_rereads:,} (additional reads)[/bold green]",
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

        # For rereads, we only count the additional reads (beyond the first read)
        # The first read is already counted in either series or standalone
        reread_books = sum(row[2] - 1 for row in data['reread'])  # Subtract first read
        # This is already just the additional words from rereads
        reread_words = sum(row[4] or 0 for row in data['reread'])

        # The total should be the sum of all categories
        total_books = series_books + standalone_books + reread_books
        total_words = series_words + standalone_words + reread_words

        # Add rows
        for category, books, words in [
            ("Series", series_books, series_words),
            ("Standalone", standalone_books, standalone_words),
            # Renamed to clarify these are only additional reads
            ("Additional Reads", reread_books, reread_words)
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

        # We'll use direct lookups with next() instead of dictionaries

        # Save series data
        series_path = csv_dir / "series.csv"
        with open(series_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Series Name', 'Author(s)',
                'Novels Read', 'Novels Unread', 'Novels Future', 'Novels Total',
                'Novellas Read', 'Novellas Unread', 'Novellas Future', 'Novellas Total',
                'Read Words', 'Unread Words', 'Total Words', 'Status'
            ])

            for row in data['series']:
                series = row[0] or "N/A"
                read_books = row[1]
                read_novels = row[4] if len(row) > 4 else 0
                read_novellas = row[5] if len(row) > 5 else 0

                # Get total counts for this series
                total_count_row = next((r for r in data['series_total'] if r[0] == series), None)
                total_books = total_count_row[1] if total_count_row else read_books
                total_novels = total_count_row[2] if total_count_row and len(total_count_row) > 2 else read_novels
                total_novellas = total_count_row[3] if total_count_row and len(total_count_row) > 3 else read_novellas

                # Get future counts for this series
                future_count_row = next((r for r in data['future_books'] if r[0] == series), None)
                future_books = future_count_row[1] if future_count_row else 0
                future_novels = future_count_row[2] if future_count_row and len(future_count_row) > 2 else 0
                future_novellas = future_count_row[3] if future_count_row and len(future_count_row) > 3 else 0

                # Get unread counts for this series
                unread_count_row = next((r for r in data['unread_books'] if r[0] == series), None)
                unread_words = unread_count_row[4] if unread_count_row and len(unread_count_row) > 4 else 0

                # Calculate unread books, excluding future/unpublished books
                unread_books = max(0, total_books - read_books - future_books)
                unread_novels = max(0, total_novels - read_novels - future_novels)
                unread_novellas = max(0, total_novellas - read_novellas - future_novellas)

                # Determine series status
                if unread_books > 0:
                    status = "Unread Books"
                elif future_books > 0:
                    status = "Future Books Only"
                else:
                    status = "Complete"

                # Calculate total words
                read_words = row[2] or 0
                total_series_words = read_words + unread_words

                writer.writerow([
                    series,
                    row[3] or "Unknown",
                    read_novels,
                    "" if unread_novels == 0 else unread_novels,
                    future_novels,
                    total_novels,
                    read_novellas,
                    "" if unread_novellas == 0 else unread_novellas,
                    future_novellas,
                    total_novellas,
                    read_words,
                    unread_words,
                    total_series_words,
                    status
                ])

        # Save standalone data
        standalone_path = csv_dir / "standalone.csv"
        with open(standalone_path, 'w', newline='', encoding='utf-8') as f:
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
        with open(reread_path, 'w', newline='', encoding='utf-8') as f:
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

            # Display color legend before the series table
            console.print("[bold]Series Color Legend:[/bold]")
            if not finished_only:
                console.print("[dim white]Gray[/dim white] = Series is not started")
            console.print("[bold red]Red[/bold red] = Series is started, but has unread novels")
            console.print("[bold orange3]Orange[/bold orange3] = Series is started, and has no unread novels, but some unread novellas")
            console.print("[bold yellow]Yellow[/bold yellow] = Series is started, and all books are read, but there are unpublished books")
            console.print("[bold green]Green[/bold green] = Series is started, and all books are published and read")
            console.print("")
            console.print("[bold]Note:[/bold] Books are classified as novels if they are ≥45,000 words, otherwise they are considered novellas.")
            console.print("")

            console.print(self._create_series_table(results['series'], results['series_total'], results['future_books'], results['unread_books']))
            console.print("\n")
            console.print(self._create_standalone_table(results['standalone']))
            console.print("\n")
            console.print(self._create_reread_table(results['reread']))
            console.print("\n")
            console.print(self._create_summary_table(results))
            console.print("\n")
