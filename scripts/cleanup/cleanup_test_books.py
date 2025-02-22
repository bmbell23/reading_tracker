from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from sqlalchemy import or_

def cleanup_test_books():
    """Remove all test books and their associated readings from the database"""
    session = SessionLocal()
    try:
        # Find all test books
        test_books = session.query(Book).filter(
            or_(
                Book.title.like('TEST_%'),
                Book.title == 'Property Test Book',
                Book.title.like('%_TEMP'),
                Book.author_name_first.like('TEST_%'),
                Book.author_name_second.like('TEST_%')
            )
        ).all()

        if not test_books:
            print("No test books found.")
            return

        # Get IDs of test books
        test_book_ids = [book.id for book in test_books]

        # Delete associated readings first
        readings_deleted = session.query(Reading).filter(
            Reading.book_id.in_(test_book_ids)
        ).delete(synchronize_session=False)

        # Delete the test books
        books_deleted = session.query(Book).filter(
            Book.id.in_(test_book_ids)
        ).delete(synchronize_session=False)

        session.commit()
        print(f"Cleaned up {books_deleted} test books and {readings_deleted} associated readings.")

    except Exception as e:
        session.rollback()
        print(f"Error during cleanup: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_test_books()