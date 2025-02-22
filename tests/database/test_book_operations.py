from datetime import date
from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from sqlalchemy import text
from .test_base import TestDatabaseBase

class TestBookOperations(TestDatabaseBase):
    def test_book_creation(self):
        """Test creating a new book with valid data"""
        new_book = Book(
            title="Test Book",
            author_name_first="John",
            author_name_second="Doe",
            word_count=80000,
            page_count=300,
            date_published=date(2023, 1, 1),
            author_gender="F",
            genre="Fantasy"
        )

        try:
            self.session.add(new_book)
            self.session.commit()

            # Fetch the book and verify
            saved_book = self.session.query(Book).filter_by(title="Test Book").first()
            self.assertIsNotNone(saved_book)
            self.assertEqual(saved_book.author, "John Doe")
            self.assertEqual(saved_book.word_count, 80000)

        except Exception as e:
            self.session.rollback()
            raise e

    def test_book_series_operations(self):
        """Test book series-related operations"""
        try:
            # Create test books in a series
            books = [
                Book(
                    title=f"TEST_SERIES_TEMP Book {i}",
                    author_name_first="Series",
                    author_name_second="Author",
                    series="TEST_SERIES_TEMP",
                    series_number=i  # Changed from series_index to series_number
                ) for i in range(1, 4)
            ]

            for book in books:
                self.session.add(book)
            self.session.commit()

            # Verify series information
            series_books = (self.session.query(Book)
                          .filter_by(series="TEST_SERIES_TEMP")
                          .order_by(Book.series_number)  # Changed from series_index to series_number
                          .all())

            self.assertEqual(len(series_books), 3)
            self.assertEqual(series_books[0].series_number, 1)
            self.assertEqual(series_books[1].series_number, 2)
            self.assertEqual(series_books[2].series_number, 3)

        except Exception as e:
            self.session.rollback()
            raise e

    def test_book_properties(self):
        """Test book property calculations"""
        book = Book(
            title="TEST_PROPERTY_BOOK_TEMP",  # More unique name
            author_name_first="Jane",
            author_name_second="Smith",
            word_count=100000,
            page_count=400,
            date_published=date(2023, 1, 1)
        )

        try:
            self.session.add(book)
            self.session.commit()

            # Test calculated properties
            self.assertEqual(book.words_per_page, 250)  # 100000/400
            self.assertEqual(book.year_published, 2023)
            self.assertEqual(book.author, "Jane Smith")
            self.assertEqual(book.author_sorted, "Smith, Jane")

        except Exception as e:
            self.session.rollback()
            raise e

    def test_book_search(self):
        """Test book search functionality"""
        try:
            # Create test books
            test_books = [
                Book(
                    title="TEST_FANTASY_ADVENTURE_TEMP",
                    author_name_first="Author",
                    author_name_second="TEST_ONE",
                    genre="Fantasy"
                ),
                Book(
                    title="TEST_SCIENCE_BOOK_TEMP",
                    author_name_first="Author",
                    author_name_second="TEST_TWO",
                    genre="Science Fiction"
                )
            ]

            for book in test_books:
                self.session.add(book)
            self.session.commit()

            # Search for fantasy books
            fantasy_books = (self.session.query(Book)
                            .filter(Book.genre == "Fantasy")
                            .filter(Book.title.like("TEST_%"))  # Only get our test books
                            .all())

            self.assertEqual(len(fantasy_books), 1)

        except Exception as e:
            self.session.rollback()
            raise e

if __name__ == '__main__':
    unittest.main()
