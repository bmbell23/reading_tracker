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

def get_media_stats(finished_only=False, csv_output=False):
    with engine.connect() as conn:
        # Base query for media statistics
        if finished_only:
            query = """
                SELECT
                    r.media,
                    COUNT(DISTINCT r.book_id) as book_count,
                    SUM(b.word_count) as total_words
                FROM read r
                INNER JOIN books b ON r.book_id = b.id
                WHERE r.date_finished_actual IS NOT NULL
                GROUP BY r.media
                ORDER BY book_count DESC
            """
        else:
            query = """
                SELECT
                    r.media,
                    COUNT(DISTINCT r.book_id) as book_count,
                    SUM(b.word_count) as total_words
                FROM read r
                INNER JOIN books b ON r.book_id = b.id
                GROUP BY r.media
                ORDER BY book_count DESC
            """

        results = conn.execute(text(query)).fetchall()

        # Calculate totals for percentages
        total_books = sum(row[1] for row in results)
        total_words = sum(row[2] or 0 for row in results)

        # Handle CSV output
        if csv_output:
            csv_dir = "csv"
            if not os.path.exists(csv_dir):
                os.makedirs(csv_dir)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            status = "finished" if finished_only else "all"
            filename = f"media_stats_{status}_{timestamp}.csv"
            filepath = os.path.join(csv_dir, filename)

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

            print(f"\nCSV file has been created: {filepath}")

        # Create Rich table
        status = "Finished" if finished_only else "All"
        table = Table(title=f"Reading Statistics by Media ({status} Books)")

        # Add columns
        table.add_column("Media", justify="left")
        table.add_column("Books", justify="right")
        table.add_column("Words", justify="right")
        table.add_column("Books %", justify="right")
        table.add_column("Words %", justify="right")

        # Add rows
        for row in results:
            media = row[0] or "Unknown"
            books = row[1]
            words = row[2] or 0
            books_percent = (books / total_books * 100) if total_books else 0
            words_percent = (words / total_words * 100) if total_words else 0

            # Define color based on media type
            if media.lower() == 'audio':
                color = 'orange1'
            elif media.lower() == 'hardcover':
                color = 'purple'
            elif media.lower() == 'kindle':
                color = 'blue'
            else:
                color = 'white'

            table.add_row(
                media,
                str(books),
                f"{words:,}",
                f"{books_percent:.1f}%",
                f"{words_percent:.1f}%",
                style=color
            )

        # Add total row
        table.add_row(
            "Total",
            str(total_books),
            f"{total_words:,}",
            "100.0%",
            "100.0%",
            style="bold white"
        )

        # Print the table
        console.print("\n")
        console.print(table)
        console.print("\n")

def main():
    parser = argparse.ArgumentParser(description='Get statistics about books read by media format')
    parser.add_argument('--finished-only', '-f',
                       action='store_true',
                       help='Only include books that have been finished reading')
    parser.add_argument('--csv', '-c',
                       action='store_true',
                       help='Output results to CSV file')

    args = parser.parse_args()
    get_media_stats(args.finished_only, args.csv)

if __name__ == "__main__":
    main()
