import sys
import os
from datetime import date
from src.queries.reading_queries import ReadingQueries

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.system('cls' if os.name == 'nt' else 'clear')


def main():
    queries = ReadingQueries()
    results = queries.get_current_unfinished_readings()
    today = date.today()

    # Show how to access specific fields
    print("\nGood Morning! The books you are currently reading are:")
    for title, author, start_date, media in results:
        print(f"- {title} by {author} on {media}, which you've been reading for "
              f"{(today - start_date).days} days.")

    print("\nHave a great day reading!\n\n")

if __name__ == "__main__":
    main()
