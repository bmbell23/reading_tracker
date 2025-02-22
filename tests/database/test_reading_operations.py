import unittest
from datetime import date, timedelta
from src.models.base import SessionLocal
from src.models.book import Book
from src.models.reading import Reading
from src.utils.constants import READING_SPEEDS, DEFAULT_WPD

class TestReadingOperations(unittest.TestCase):
    def setUp(self):
        self.session = SessionLocal()
        # Create a test book with a more distinctive name
        self.test_book = Book(
            title="TEST_READING_OPERATIONS_TEMP",
            author_name_first="TEST",
            author_name_second="AUTHOR_TEMP",
            word_count=80000,
            page_count=300
        )
        self.session.add(self.test_book)
        self.session.commit()

    def tearDown(self):
        # Clean up test data
        readings = self.session.query(Reading).filter_by(book_id=self.test_book.id).all()
        for reading in readings:
            self.session.delete(reading)
        self.session.delete(self.test_book)
        self.session.commit()
        self.session.close()

    def test_reading_creation(self):
        """Test creating a new reading entry"""
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

        saved_reading = (self.session.query(Reading)
                        .filter_by(book_id=self.test_book.id)
                        .first())

        self.assertEqual(saved_reading.media, "Kindle")
        self.assertEqual(saved_reading.rating_enjoyment, 8.5)
        self.assertEqual(saved_reading.book.title, "TEST_READING_OPERATIONS_TEMP")

    def test_reading_calculations(self):
        """Test reading time calculations"""
        start_date = date.today() - timedelta(days=10)
        reading = Reading(
            book_id=self.test_book.id,
            media="Kindle",
            date_started=start_date,
            date_finished_actual=date.today()
        )

        self.session.add(reading)
        self.session.commit()

        # Test days_estimate calculation
        expected_days = int(self.test_book.word_count /
                          READING_SPEEDS.get('kindle', DEFAULT_WPD))
        self.assertEqual(reading.days_estimate, expected_days)

        # Test days_elapsed_to_read calculation
        self.assertEqual(reading.days_elapsed_to_read, 10)

        # Test days_to_read_delta_from_estimate calculation
        self.assertEqual(
            reading.days_to_read_delta_from_estimate,
            10 - expected_days
        )

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
