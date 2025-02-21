import sys
import os
from datetime import date, timedelta
from tabulate import tabulate
from src.queries.reading_queries import ReadingQueries

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    queries = ReadingQueries()
    results = queries.get_current_unfinished_readings()
    today = date.today()

    # Prepare table data
    table_data = []

    for reading in results:
        author = f"{reading.book.author_name_first or ''} {reading.book.author_name_second or ''}".strip()
        days_elapsed = (today - reading.date_started).days
        days_remaining = reading.days_estimate - days_elapsed if reading.days_estimate else None
        est_end_date = today + timedelta(days=days_remaining) if days_remaining else None

        # Calculate estimated progress
        if days_remaining is not None and reading.book.page_count:
            total_days = days_elapsed + days_remaining
            progress_pct = (days_elapsed / total_days) if total_days > 0 else 0
            est_pages = int(progress_pct * reading.book.page_count)
            progress_str = f"{progress_pct:.0%} (p. {est_pages})"
        else:
            progress_str = "Unknown"

        table_data.append([
            reading.media,
            reading.book.title,
            author,
            reading.date_started.strftime('%Y-%m-%d'),
            progress_str,
            days_elapsed,
            days_remaining or 'Unknown',
            est_end_date.strftime('%Y-%m-%d') if est_end_date else 'Unknown'
        ])

    # Sort by media type and then title
    table_data.sort(key=lambda x: (x[0], x[1]))

    headers = ['Format', 'Title', 'Author', 'Start\nDate',
              'Est.\nProgress', 'Days\nElapsed', 'Days\nto Finish', 'Est.\nEnd Date']

    if table_data:
        print("\nCurrent Reading Sessions:")
        print(tabulate(
            table_data,
            headers=headers,
            tablefmt='grid',
            colalign=('center', 'center', 'center', 'center', 'center', 'center', 'center', 'center')
        ))
    else:
        print("\nNo active reading sessions found.")
    print("\n")

if __name__ == "__main__":
    main()
