from pathlib import Path
from typing import List, Optional
from src.models import SessionLocal, Book, Reading, Inventory
from src.utils.path_utils import get_project_root

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

if __name__ == "__main__":
    cleanup_test_data()
    removed_files = remove_test_files()
    print(f"Removed {len(removed_files)} test files")
