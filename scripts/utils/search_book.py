import sys
from pathlib import Path
from scripts.utils.paths import find_project_root

# Add project root to Python path
project_root = find_project_root()
sys.path.insert(0, str(project_root))

from src.models.base import SessionLocal
from src.models.book import Book
import argparse
from scripts.queries.common_queries import CommonQueries

def main():
    parser = argparse.ArgumentParser(description='Search for book readings by title')
    parser.add_argument('title', help='Book title to search for')
    parser.add_argument('--fuzzy', '-f', action='store_true',
                       help='Use fuzzy matching instead of exact title match')

    args = parser.parse_args()

    queries = CommonQueries()
    queries.print_readings_by_title(args.title, not args.fuzzy)

if __name__ == "__main__":
    main()
