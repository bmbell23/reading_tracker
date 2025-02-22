import sys
import os
import argparse
import csv
from datetime import datetime
from src.models.base import engine
from sqlalchemy import text

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
        series_total_books = 0
        series_total_words = 0
        for row in series_results:
            book_count = row[1]
            total_words = row[2] or 0
            series_total_books += book_count
            series_total_words += total_words

        standalone_total_words = 0
        for row in standalone_results:
            words = row[2] or 0
            standalone_total_words += words

        reread_total_additional_words = 0
        reread_total_books = len(reread_results)
        for row in reread_results:
            additional_words = row[4] or 0
            reread_total_additional_words += additional_words

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

            print(f"\nCSV files have been created in: {output_dir}")

        # Print results to console
        status = "Finished" if finished_only else "All"

        # Print series results
        print(f"\nSeries Statistics ({status} Books, Ordered by Total Word Count):")
        print("-" * 140)
        print(f"{'Series Name':<40}\t{'Author(s)':<40}\t{'Books':>8}\t{'Total Words':>15}")
        print("-" * 140)

        for row in series_results:
            series_name = row[0] or "N/A"
            book_count = row[1]
            total_words = row[2] or 0
            author = row[3] or "Unknown"
            formatted_words = f"{total_words:,}" if total_words else "N/A"
            print(f"{series_name:<40}\t{author:<40}\t{book_count:>8}\t{formatted_words:>15}")

        print("-" * 140)
        print(f"Total Series: {len(series_results)}")
        print(f"Total Books in Series: {series_total_books}")
        print(f"Total Words Across All Series: {series_total_words:,}")

        # Print standalone books
        print(f"\nStandalone Books ({status}):")
        print("-" * 100)
        print(f"{'Title':<50}\t{'Author':>30}\t{'Words':>15}")
        print("-" * 100)

        for row in standalone_results:
            title = row[0] or "N/A"
            author = row[1] or "Unknown"
            words = row[2] or 0
            formatted_words = f"{words:,}" if words else "N/A"
            print(f"{title:<50}\t{author:>30}\t{formatted_words:>15}")

        print("-" * 100)
        print(f"Total Standalone Books: {len(standalone_results)}")
        print(f"Total Words Across Standalone Books: {standalone_total_words:,}")

        # Print reread books
        print(f"\nReread Books ({status}):")
        print("-" * 120)
        print(f"{'Title':<50}\t{'Author':>30}\t{'Times Read':>10}\t{'Additional Words':>15}")
        print("-" * 120)

        for row in reread_results:
            title = row[0] or "N/A"
            author = row[1] or "Unknown"
            times_read = row[2]
            additional_words = row[4] or 0
            formatted_additional_words = f"{additional_words:,}" if additional_words else "N/A"
            print(f"{title:<50}\t{author:>30}\t{times_read:>10}\t{formatted_additional_words:>15}")

        print("-" * 120)
        print(f"Total Books Reread: {reread_total_books}")
        print(f"Total Additional Words from Rereads: {reread_total_additional_words:,}")

        # Print grand total
        print(f"\nGrand Total (Including Rereads):")
        print(f"Total Books: {series_total_books + len(standalone_results) + reread_total_books}")
        total_words = series_total_words + standalone_total_words + reread_total_additional_words
        print(f"Total Words: {total_words:,}")

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
