import unittest
from sqlalchemy import create_engine, text
from src.models.base import Base, SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from sqlalchemy import or_

class TestDatabaseBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create tables before running any tests"""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)

    def setUp(self):
        """Set up a new session for each test"""
        self.session = SessionLocal()
        self.cleanup_test_data()  # Clean up any leftover test data before each test

    def tearDown(self):
        """Clean up after each test"""
        self.cleanup_test_data()  # Clean up test data after each test
        self.session.close()

    def cleanup_test_data(self):
        """Clean up any test data"""
        try:
            # Delete readings associated with test books first
            self.session.query(Reading).filter(
                Reading.book_id.in_(
                    self.session.query(Book.id).filter(
                        or_(
                            Book.title.like('TEST_%'),
                            Book.title == 'Property Test Book',
                            Book.title.like('%_TEMP'),
                            Book.author_name_first.like('TEST_%'),
                            Book.author_name_second.like('TEST_%')
                        )
                    )
                )
            ).delete(synchronize_session=False)

            # Then delete test books
            self.session.query(Book).filter(
                or_(
                    Book.title.like('TEST_%'),
                    Book.title == 'Property Test Book',
                    Book.title.like('%_TEMP'),
                    Book.author_name_first.like('TEST_%'),
                    Book.author_name_second.like('TEST_%')
                )
            ).delete(synchronize_session=False)

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
