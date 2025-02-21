import sys
import os
from datetime import date
from src.queries.reading_queries import ReadingQueries

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    queries = ReadingQueries()
    results = queries.get_current_unfinished_readings()
    today = date.today()

    print("\nGood Morning! The books you are currently reading are:")
    for reading in results:
        author = f"{reading.book.author_name_first or ''} {reading.book.author_name_second or ''}".strip()
        estimate = f"(estimated {reading.days_estimate - (today - reading.date_started).days} days to complete)" if reading.days_estimate else ""

        print(f"- {reading.book.title} by {author} on {reading.media}, "
              f"which you've been reading for {(today - reading.date_started).days} days "
              f"{estimate}")

    print("\nHave a great day reading!\n\n")

if __name__ == "__main__":
    main()
