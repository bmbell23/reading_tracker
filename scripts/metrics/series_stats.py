import sys
import os
import argparse
import csv
from datetime import datetime
from src.models.base import engine
from sqlalchemy import text
from rich.console import Console
from rich.table import Table

console = Console()

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def write_to_csv(data, headers, filepath):
    """Write data to CSV file, creating directories if needed"""
    # Ensure the directory exists
    directory = os.path.dirname(filepath)
    ensure_directory_exists(directory)

    # Write the CSV file
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)

def get_series_stats(finished_only=False, csv_output=False):
    with engine.connect() as conn:
        # Base query for series books
        if finished_only:
            series_query = """
                SELECT
                    b.series,
                    COUNT(DISTINCT b.id) as book_count,
                    SUM(b.word_count) as total_words,
                    GROUP_CONCAT(DISTINCT b.author_name_first || ' ' || b.author_name_second) as author
                FROM books b
                INNER JOIN read r ON b.id = r.book_id
                WHERE r.date_finished_actual IS NOT NULL
                    AND b.series IS NOT NULL
                GROUP BY b.series
                ORDER BY total_words DESC
            """

            # Query for standalone books
            standalone_query = """
                SELECT
                    b.title,
                    b.author_name_first || ' ' || b.author_name_second as author,
                    b.word_count
                FROM books b
                INNER JOIN read r ON b.id = r.book_id
                WHERE r.date_finished_actual IS NOT NULL
                    AND b.series IS NULL
                ORDER BY b.word_count DESC
            """
        else:
            series_query = """
                SELECT
                    b.series,
                    COUNT(*) as book_count,
                    SUM(b.word_count) as total_words,
                    GROUP_CONCAT(DISTINCT b.author_name_first || ' ' || b.author_name_second) as author
                FROM books b
                WHERE b.series IS NOT NULL
                GROUP BY b.series
                ORDER BY total_words DESC
            """

            # Query for standalone books
            standalone_query = """
                SELECT
                    b.title,
                    b.author_name_first || ' ' || b.author_name_second as author,
                    b.word_count
                FROM books b
                WHERE b.series IS NULL
                ORDER BY b.word_count DESC
            """

        # Query for rereads
        if finished_only:
            reread_query = """
                SELECT
                    b.title,
                    b.author_name_first || ' ' || b.author_name_second as author,
                    COUNT(*) as times_read,
                    b.word_count,
                    (COUNT(*) * b.word_count) - b.word_count as additional_words
                FROM books b
                INNER JOIN read r ON b.id = r.book_id
                WHERE r.date_finished_actual IS NOT NULL
                GROUP BY b.id, b.title, b.author_name_first, b.author_name_second, b.word_count
                HAVING COUNT(*) > 1
                ORDER BY additional_words DESC
            """
        else:
            reread_query = """
                SELECT
                    b.title,
                    b.author_name_first || ' ' || b.author_name_second as author,
                    COUNT(*) as times_read,
                    b.word_count,
                    (COUNT(*) * b.word_count) - b.word_count as additional_words
                FROM books b
                INNER JOIN read r ON b.id = r.book_id
                GROUP BY b.id, b.title, b.author_name_first, b.author_name_second, b.word_count
                HAVING COUNT(*) > 1
                ORDER BY additional_words DESC
            """

        # Execute queries
        series_results = conn.execute(text(series_query)).fetchall()
        standalone_results = conn.execute(text(standalone_query)).fetchall()
        reread_results = conn.execute(text(reread_query)).fetchall()

        # Calculate totals
        series_total_books = sum(row[1] for row in series_results)
        series_total_words = sum(row[2] or 0 for row in series_results)
        standalone_total_words = sum(row[2] or 0 for row in standalone_results)
        reread_total_additional_words = sum(row[4] or 0 for row in reread_results)
        reread_total_books = len(reread_results)

        # Handle CSV output
        if csv_output:
            # Create base directories
            csv_dir = "csv"
            ensure_directory_exists(csv_dir)

            # Create timestamped subfolder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            status = "finished" if finished_only else "all"
            subfolder = f"reading_stats_{status}_{timestamp}"
            output_dir = os.path.join(csv_dir, subfolder)
            ensure_directory_exists(output_dir)

            # Write series data
            series_data = [(
                row[0] or "N/A",
                row[3] or "Unknown",
                row[1],
                row[2] or 0
            ) for row in series_results]
            write_to_csv(
                series_data,
                ['Series Name', 'Author(s)', 'Book Count', 'Total Words'],
                os.path.join(output_dir, "series.csv")
            )

            # Write standalone data
            standalone_data = [(
                row[0] or "N/A",
                row[1] or "Unknown",
                row[2] or 0
            ) for row in standalone_results]
            write_to_csv(
                standalone_data,
                ['Title', 'Author', 'Word Count'],
                os.path.join(output_dir, "standalone.csv")
            )

            # Write reread data
            reread_data = [(
                row[0] or "N/A",
                row[1] or "Unknown",
                row[2],
                row[4] or 0
            ) for row in reread_results]
            write_to_csv(
                reread_data,
                ['Title', 'Author', 'Times Read', 'Additional Words'],
                os.path.join(output_dir, "rereads.csv")
            )

            # Write summary data
            summary_data = [
                ['Category', 'Count', 'Words'],
                ['Series Total', len(series_results), series_total_words],
                ['Standalone Total', len(standalone_results), standalone_total_words],
                ['Reread Total', reread_total_books, reread_total_additional_words],
                ['Grand Total', series_total_books + len(standalone_results) + reread_total_books,
                 series_total_words + standalone_total_words + reread_total_additional_words]
            ]
            write_to_csv(
                summary_data,
                [],
                os.path.join(output_dir, "summary.csv")
            )

            console.print(f"\nCSV files have been created in: [blue]{output_dir}[/blue]")

        # Print results using Rich tables
        status = "Finished" if finished_only else "All"

        # Series table
        series_table = Table(
            title=f"Series Statistics ({status} Books, Ordered by Total Word Count)",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_black"
        )
        series_table.add_column("Series Name", justify="left")
        series_table.add_column("Author(s)", justify="left")
        series_table.add_column("Books", justify="right")
        series_table.add_column("Total Words", justify="right")

        for row in series_results:
            series_table.add_row(
                row[0] or "N/A",
                row[3] or "Unknown",
                str(row[1]),
                f"{row[2]:,}" if row[2] else "N/A"
            )

        series_table.add_row(
            "TOTAL",
            "",
            str(series_total_books),
            f"{series_total_words:,}",
            style="bold white"
        )

        # Standalone table
        standalone_table = Table(
            title=f"\nStandalone Books ({status})",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_black"
        )
        standalone_table.add_column("Title", justify="left")
        standalone_table.add_column("Author", justify="left")
        standalone_table.add_column("Words", justify="right")

        for row in standalone_results:
            standalone_table.add_row(
                row[0] or "N/A",
                row[1] or "Unknown",
                f"{row[2]:,}" if row[2] else "N/A"
            )

        standalone_table.add_row(
            "TOTAL",
            "",
            f"{standalone_total_words:,}",
            style="bold white"
        )

        # Reread table
        reread_table = Table(
            title=f"\nReread Books ({status})",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_black"
        )
        reread_table.add_column("Title", justify="left")
        reread_table.add_column("Author", justify="left")
        reread_table.add_column("Times Read", justify="right")
        reread_table.add_column("Additional Words", justify="right")

        for row in reread_results:
            reread_table.add_row(
                row[0] or "N/A",
                row[1] or "Unknown",
                str(row[2]),
                f"{row[4]:,}" if row[4] else "N/A"
            )

        reread_table.add_row(
            "TOTAL",
            "",
            str(reread_total_books),
            f"{reread_total_additional_words:,}",
            style="bold white"
        )

        # Summary table
        summary_table = Table(
            title="\nGrand Total (Including Rereads)",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_black"
        )
        summary_table.add_column("Category", justify="left")
        summary_table.add_column("Books", justify="right")
        summary_table.add_column("Words", justify="right")

        total_books = series_total_books + len(standalone_results) + reread_total_books
        total_words = series_total_words + standalone_total_words + reread_total_additional_words

        summary_table.add_row("Series", str(series_total_books), f"{series_total_words:,}")
        summary_table.add_row("Standalone", str(len(standalone_results)), f"{standalone_total_words:,}")
        summary_table.add_row("Reread", str(reread_total_books), f"{reread_total_additional_words:,}")
        summary_table.add_row("TOTAL", str(total_books), f"{total_words:,}", style="bold white")

        # Print all tables
        console.print("\n")
        console.print(series_table)
        console.print("\n")
        console.print(standalone_table)
        console.print("\n")
        console.print(reread_table)
        console.print("\n")
        console.print(summary_table)
        console.print("\n")

def main():
    parser = argparse.ArgumentParser(description='Get statistics about book series')
    parser.add_argument('--finished-only', '-f',
                       action='store_true',
                       help='Only include books that have been finished reading')
    parser.add_argument('--csv', '-c',
                       action='store_true',
                       help='Output results to CSV files')

    args = parser.parse_args()
    get_series_stats(args.finished_only, args.csv)

if __name__ == "__main__":
    main()
