from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from src.models.inventory import Inventory

def cleanup_test_data():
    session = SessionLocal()
    try:
        # Find test books
        test_books = session.query(Book).filter(
            Book.title.in_([
                "Reading Test Book",
                "Inventory Test Book",
                "Test Book",
                "Property Test Book",
                "TEST_READING_OPERATIONS_TEMP",
                "TEST_INVENTORY_OPERATIONS_TEMP"
            ])
        ).all()

        # Store book IDs
        book_ids = [book.id for book in test_books]

        # First delete all readings for these books
        session.query(Reading).filter(
            Reading.book_id.in_(book_ids)
        ).delete(synchronize_session=False)

        # Then delete all inventory entries for these books
        session.query(Inventory).filter(
            Inventory.book_id.in_(book_ids)
        ).delete(synchronize_session=False)

        # Finally delete the books
        session.query(Book).filter(
            Book.id.in_(book_ids)
        ).delete(synchronize_session=False)

        session.commit()
        print(f"Cleaned up {len(test_books)} test books and their associated data")

    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_test_data()
