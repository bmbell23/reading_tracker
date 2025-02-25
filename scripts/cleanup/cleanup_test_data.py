from pathlib import Path
from typing import List, Optional
# Keep the correct relative imports
from src.models import SessionLocal, Book, Reading, Inventory
from src.utils.path_utils import get_project_root
import argparse

def cleanup_test_data() -> None:
    """Remove test data from the database."""
    session = SessionLocal()
    try:
        # Get test books first
        test_books = session.query(Book).filter(
            Book.title.like('TEST_%')
        ).all()

        # Remove readings associated with test books
        session.query(Reading).filter(
            Reading.book_id.in_([book.id for book in test_books])
        ).delete(synchronize_session=False)

        # Remove test inventory entries associated with test books
        session.query(Inventory).filter(
            Inventory.book_id.in_([book.id for book in test_books])
        ).delete(synchronize_session=False)

        # Remove test books
        session.query(Book).filter(
            Book.title.like('TEST_%')
        ).delete(synchronize_session=False)

        session.commit()
    finally:
        session.close()

def remove_test_files() -> List[Path]:
    """Remove test-related files from the project."""
    root = get_project_root()
    test_files = list(root.glob("**/*_test.*"))

    for file in test_files:
        if file.is_file():
            file.unlink()

    return test_files

def main():
    parser = argparse.ArgumentParser(description="Clean up test data and files")
    parser.add_argument('--check', action='store_true',
                       help='Run in check mode without making changes')
    args = parser.parse_args()

    if args.check:
        print("Running in check mode - no changes will be made")
        # Only print what would be removed
        session = SessionLocal()
        test_books = session.query(Book).filter(Book.title.like('TEST_%')).all()
        test_files = list(get_project_root().glob("**/*_test.*"))
        print(f"Would remove {len(test_books)} test books")
        print(f"Would remove {len(test_files)} test files")
        session.close()
    else:
        cleanup_test_data()
        removed_files = remove_test_files()
        print(f"Removed {len(removed_files)} test files")

if __name__ == "__main__":
    main()
