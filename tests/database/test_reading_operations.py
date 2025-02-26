from datetime import date, timedelta
from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from src.utils.constants import READING_SPEEDS, DEFAULT_WPD
from sqlalchemy import text
from .test_base import TestDatabaseBase

class TestReadingOperations(TestDatabaseBase):
    def setUp(self):
        super().setUp()
        # Create a test book
        self.test_book = Book(
            title="TEST_READING_OPERATIONS_TEMP",
            author_name_first="TEST",
            author_name_second="AUTHOR_TEMP",
            word_count=80000,
            page_count=300
        )
        self.session.add(self.test_book)
        self.session.commit()
        self.session.refresh(self.test_book)

    def test_reading_creation(self):
        """Test creating a new reading entry"""
        try:
            reading = Reading(
                book_id=self.test_book.id,
                media="Kindle",
                date_started=date.today(),
                date_est_start=date.today(),
                rating_enjoyment=8.5,
                rating_writing=7.5,
                rating_characters=8.0
            )

            self.session.add(reading)
            self.session.commit()

            # Clear the session to ensure we get fresh data
            self.session.expire_all()

            # Query to verify - make sure to get a fresh instance
            saved_reading = (self.session.query(Reading)
                            .filter_by(book_id=self.test_book.id)
                            .first())

            self.assertIsNotNone(saved_reading, "Reading not found after save")
            self.assertEqual(saved_reading.media, "Kindle")
            self.assertEqual(saved_reading.rating_enjoyment, 8.5)
            self.assertEqual(saved_reading.book.title, "TEST_READING_OPERATIONS_TEMP")

        except Exception as e:
            self.session.rollback()
            raise e

    def test_reading_calculations(self):
        """Test reading time calculations"""
        start_date = date.today() - timedelta(days=10)
        reading = Reading(
            book_id=self.test_book.id,
            media="Kindle",
            date_started=start_date
        )
        self.session.add(reading)
        self.session.commit()

        # Add your test assertions here

    def test_reading_chain(self):
        """Test reading chain functionality"""
        # Create a chain of readings
        reading1 = Reading(
            book_id=self.test_book.id,
            media="Physical",
            date_started=date(2023, 1, 1),
            date_finished_actual=date(2023, 1, 15)
        )
        self.session.add(reading1)
        self.session.commit()

        reading2 = Reading(
            book_id=self.test_book.id,
            media="Audio",
            date_started=date(2023, 2, 1),
            date_finished_actual=date(2023, 2, 15),
            id_previous=reading1.id
        )
        self.session.add(reading2)
        self.session.commit()

        # Test chain relationships
        self.assertEqual(reading2.previous_reading, reading1)
        self.assertEqual(reading1.subsequent_readings[0], reading2)

    def test_date_calculations(self):
        """Test date-related calculations"""
        reading = Reading(
            book_id=self.test_book.id,
            media="Kindle",
            date_started=date.today(),
            date_est_start=date.today()
        )
        self.session.add(reading)
        self.session.commit()

        # Test date_finished_estimate calculation
        if reading.days_estimate:
            expected_finish = reading.date_started + timedelta(days=reading.days_estimate)
            self.assertEqual(reading.date_finished_estimate, expected_finish)

    def test_reading_ratings(self):
        """Test reading ratings functionality"""
        reading = Reading(
            book_id=self.test_book.id,
            media="Physical",
            rating_horror=7.0,
            rating_spice=6.5,
            rating_world_building=8.0,
            rating_writing=8.5,
            rating_characters=9.0,
            rating_readability=7.5,
            rating_enjoyment=8.5
        )
        self.session.add(reading)
        self.session.commit()

        saved_reading = self.session.query(Reading).get(reading.id)
        self.assertEqual(saved_reading.rating_horror, 7.0)
        self.assertEqual(saved_reading.rating_world_building, 8.0)
        self.assertEqual(saved_reading.rating_enjoyment, 8.5)

    def test_invalid_media_type(self):
        """Test handling of invalid media types"""
        reading = Reading(
            book_id=self.test_book.id,
            media="InvalidType",
            date_started=date.today()
        )
        self.session.add(reading)
        self.session.commit()

        # Should use DEFAULT_WPD for invalid media type
        self.assertEqual(
            reading.days_estimate,
            int(self.test_book.word_count / DEFAULT_WPD)
        )

if __name__ == '__main__':
    unittest.main()
