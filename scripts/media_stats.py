import sys
import os
import argparse
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.base import engine
from sqlalchemy import text

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

        # Print results to console
        status = "Finished" if finished_only else "All"
        print(f"\nReading Statistics by Media ({status} Books):")
        print("-" * 80)
        print(f"{'Media':<15} {'Books':>8} {'Words':>12} {'Books %':>10} {'Words %':>10}")
        print("-" * 80)

        for row in results:
            media = row[0] or "Unknown"
            books = row[1]
            words = row[2] or 0
            books_percent = (books / total_books * 100) if total_books else 0
            words_percent = (words / total_words * 100) if total_words else 0

            print(f"{media:<15} {books:>8} {words:>12,} {books_percent:>9.1f}% {words_percent:>9.1f}%")

        print("-" * 80)
        print(f"{'Total:':<15} {total_books:>8} {total_words:>12,}")

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