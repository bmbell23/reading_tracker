import unittest
from datetime import date
from src.models.base import SessionLocal
from src.models.book import Book

class TestBookOperations(unittest.TestCase):
    def setUp(self):
        self.session = SessionLocal()
        # Clean up any leftover test data
        self.cleanup_test_data()

    def tearDown(self):
        self.session.close()

    def cleanup_test_data(self):
        """Clean up any test data that might be left over"""
        # Clean up series test data
        for book in self.session.query(Book).filter_by(series="TEST_SERIES_TEMP").all():
            self.session.delete(book)

        # Clean up search test data
        test_titles = [
            "TEST_FANTASY_ADVENTURE_TEMP",
            "TEST_SCIENCE_BOOK_TEMP",
            "TEST_MYSTERY_CASE_TEMP"
        ]
        for book in self.session.query(Book).filter(Book.title.in_(test_titles)).all():
            self.session.delete(book)

        self.session.commit()

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

        self.session.add(new_book)
        self.session.commit()

        # Fetch the book and verify
        saved_book = self.session.query(Book).filter_by(title="Test Book").first()
        self.assertIsNotNone(saved_book)
        self.assertEqual(saved_book.author, "John Doe")
        self.assertEqual(saved_book.word_count, 80000)

        # Cleanup
        self.session.delete(saved_book)
        self.session.commit()

    def test_book_series_operations(self):
        """Test book series-related operations"""
        try:
            # Create books in a series
            books = [
                Book(
                    title=f"TEST_SERIES_BOOK_{i}_TEMP",
                    author_name_first="Series",
                    author_name_second="Author",
                    series="TEST_SERIES_TEMP",
                    series_number=i,
                    word_count=80000,
                    page_count=300
                ) for i in range(1, 4)
            ]

            for book in books:
                self.session.add(book)
            self.session.commit()

            # Test series queries
            series_books = (self.session.query(Book)
                           .filter_by(series="TEST_SERIES_TEMP")
                           .order_by(Book.series_number)
                           .all())

            self.assertEqual(len(series_books), 3)
            self.assertEqual(series_books[0].series_number, 1)
            self.assertEqual(series_books[-1].series_number, 3)

        finally:
            # Cleanup - delete all books created in this test
            for book in self.session.query(Book).filter_by(series="TEST_SERIES_TEMP").all():
                self.session.delete(book)
            self.session.commit()

    def test_book_properties(self):
        """Test book property calculations"""
        book = Book(
            title="Property Test Book",
            author_name_first="Jane",
            author_name_second="Smith",
            word_count=100000,
            page_count=400,
            date_published=date(2023, 1, 1)
        )

        self.session.add(book)
        self.session.commit()

        # Test calculated properties
        self.assertEqual(book.words_per_page, 250)  # 100000/400
        self.assertEqual(book.year_published, 2023)
        self.assertEqual(book.author, "Jane Smith")
        self.assertEqual(book.author_sorted, "Smith, Jane")

        # Cleanup
        self.session.delete(book)
        self.session.commit()

    def test_book_search(self):
        """Test book search functionality"""
        try:
            # First ensure cleanup of any previous test data
            self.cleanup_test_data()

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
                ),
                Book(
                    title="TEST_MYSTERY_CASE_TEMP",
                    author_name_first="Author",
                    author_name_second="TEST_ONE",
                    genre="Mystery"
                )
            ]

            for book in test_books:
                self.session.add(book)
            self.session.commit()

            # Debug: Let's see what fantasy books exist
            all_fantasy = (self.session.query(Book)
                          .filter(Book.genre == "Fantasy")
                          .all())
            print("\nAll fantasy books:", [book.title for book in all_fantasy])

            # Test author search
            author_books = (self.session.query(Book)
                           .filter_by(author_name_second="TEST_ONE")
                           .all())
            self.assertEqual(len(author_books), 2)

            # Test genre search with more specific filtering
            fantasy_books = (self.session.query(Book)
                            .filter(
                                Book.genre == "Fantasy",
                                Book.title.like("TEST_%_TEMP")  # More specific pattern
                            )
                            .all())
            print("\nTest fantasy books:", [book.title for book in fantasy_books])
            self.assertEqual(len(fantasy_books), 1)

            # Test title search (partial match)
            case_books = (self.session.query(Book)
                         .filter(Book.title == "TEST_MYSTERY_CASE_TEMP")  # Exact match
                         .all())
            self.assertEqual(len(case_books), 1)

        finally:
            # Cleanup - delete all books created in this test
            test_titles = [
                "TEST_FANTASY_ADVENTURE_TEMP",
                "TEST_SCIENCE_BOOK_TEMP",
                "TEST_MYSTERY_CASE_TEMP"
            ]
            for book in self.session.query(Book).filter(Book.title.in_(test_titles)).all():
                self.session.delete(book)
            self.session.commit()

            # Verify cleanup
            remaining_test_books = (self.session.query(Book)
                                  .filter(Book.title.like("TEST_%_TEMP"))
                                  .all())
            if remaining_test_books:
                print("\nWarning: Test books remaining after cleanup:",
                      [book.title for book in remaining_test_books])

if __name__ == '__main__':
    unittest.main()
