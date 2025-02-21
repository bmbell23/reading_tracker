import sys
import os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.base import engine
from sqlalchemy import text

def get_series_stats(finished_only=False):
    with engine.connect() as conn:
        # Base query for series books
        if finished_only:
            series_query = """
                SELECT
                    series,
                    COUNT(DISTINCT b.id) as book_count,
                    SUM(DISTINCT b.word_count) as total_words
                FROM books b
                INNER JOIN read r ON b.id = r.book_id
                WHERE r.date_finished_actual IS NOT NULL
                    AND series IS NOT NULL
                GROUP BY series
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
                    AND series IS NULL
                ORDER BY b.word_count DESC
            """
        else:
            series_query = """
                SELECT
                    series,
                    COUNT(*) as book_count,
                    SUM(word_count) as total_words
                FROM books b
                WHERE series IS NOT NULL
                GROUP BY series
                ORDER BY total_words DESC
            """

            # Query for standalone books
            standalone_query = """
                SELECT
                    title,
                    author_name_first || ' ' || author_name_second as author,
                    word_count
                FROM books b
                WHERE series IS NULL
                ORDER BY word_count DESC
            """

        # New query for rereads
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

        # Print series results
        status = "Finished" if finished_only else "All"
        print(f"\nSeries Statistics ({status} Books, Ordered by Total Word Count):")
        print("-" * 100)
        print(f"{'Series Name':<50}\t{'Books':>8}\t{'Total Words':>15}")
        print("-" * 100)

        series_total_books = 0
        series_total_words = 0

        for row in series_results:
            series_name = row[0] or "N/A"
            book_count = row[1]
            total_words = row[2] or 0
            series_total_books += book_count
            series_total_words += total_words

            # Format word count with commas
            formatted_words = f"{total_words:,}" if total_words else "N/A"

            # Using tabs and fixed widths for better alignment
            print(f"{series_name:<50}\t{book_count:>8}\t{formatted_words:>15}")

        # Print series summary
        print("-" * 100)
        print(f"\nSeries Summary:")
        print(f"Total Series: {len(series_results)}")
        print(f"Total Books in Series: {series_total_books}")
        print(f"Total Words Across All Series: {series_total_words:,}")

        # Print standalone books
        print(f"\nStandalone Books ({status}):")
        print("-" * 100)
        print(f"{'Title':<50}\t{'Author':>30}\t{'Words':>15}")
        print("-" * 100)

        standalone_total_words = 0

        for row in standalone_results:
            title = row[0] or "N/A"
            author = row[1] or "Unknown"
            words = row[2] or 0
            standalone_total_words += words

            # Format word count with commas
            formatted_words = f"{words:,}" if words else "N/A"

            # Using tabs and fixed widths for better alignment
            print(f"{title:<50}\t{author:>30}\t{formatted_words:>15}")

        # Print standalone summary
        print("-" * 100)
        print(f"\nStandalone Books Summary:")
        print(f"Total Standalone Books: {len(standalone_results)}")
        print(f"Total Words Across Standalone Books: {standalone_total_words:,}")

        # Print reread books
        print(f"\nReread Books ({status}):")
        print("-" * 120)
        print(f"{'Title':<50}\t{'Author':>30}\t{'Times Read':>10}\t{'Additional Words':>15}")
        print("-" * 120)

        reread_total_additional_words = 0
        reread_total_books = len(reread_results)

        for row in reread_results:
            title = row[0] or "N/A"
            author = row[1] or "Unknown"
            times_read = row[2]
            additional_words = row[4] or 0
            reread_total_additional_words += additional_words

            # Format word count with commas
            formatted_additional_words = f"{additional_words:,}" if additional_words else "N/A"

            # Using tabs and fixed widths for better alignment
            print(f"{title:<50}\t{author:>30}\t{times_read:>10}\t{formatted_additional_words:>15}")

        # Print reread summary
        print("-" * 120)
        print(f"\nReread Books Summary:")
        print(f"Total Books Reread: {reread_total_books}")
        print(f"Total Additional Words from Rereads: {reread_total_additional_words:,}")

        # Print updated grand total
        print(f"\nGrand Total (Including Rereads):")
        print(f"Total Books: {series_total_books + len(standalone_results) + reread_total_books}")
        total_words = series_total_words + standalone_total_words + reread_total_additional_words
        print(f"Total Words: {total_words:,}")

def main():
    parser = argparse.ArgumentParser(description='Get statistics about book series')
    parser.add_argument('--finished-only', '-f',
                       action='store_true',
                       help='Only include books that have been finished reading')

    args = parser.parse_args()
    get_series_stats(args.finished_only)

if __name__ == "__main__":
    main()
