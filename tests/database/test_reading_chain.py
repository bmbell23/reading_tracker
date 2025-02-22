import unittest
from datetime import date
from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book

class TestReadingChain(unittest.TestCase):
    def setUp(self):
        self.session = SessionLocal()

    def tearDown(self):
        self.session.close()

    def _get_current_reading_by_media(self, media_type):
        """Get the current reading for a specific media type"""
        return (self.session.query(Reading)
                .join(Book)
                .filter(Reading.media.ilike(f"%{media_type}%"))
                .filter(Reading.date_started <= date.today())
                .filter(Reading.date_finished_actual.is_(None))
                .first())

    def _verify_chain(self, start_reading, num_books=None, direction="backward"):
        """
        Verify the reading chain for completeness
        Args:
            start_reading: Reading object to start from
            num_books: Number of books to check (None for all)
            direction: 'backward' or 'forward'
        Returns:
            list of tuples (reading_id, error_message) for any issues found
        """
        if not start_reading:
            return [("None", "No starting reading found")]

        errors = []
        current = start_reading
        books_checked = 0

        while current and (num_books is None or books_checked < num_books):
            # Check for missing dates
            if not current.date_est_start:
                errors.append((current.id, f"Missing est_start date for '{current.book.title}'"))
            if not current.date_est_end:
                errors.append((current.id, f"Missing est_end date for '{current.book.title}'"))

            # Move to next reading based on direction
            if direction == "backward":
                if not current.id_previous:
                    break
                current = self.session.get(Reading, current.id_previous)
            else:  # forward
                current = (self.session.query(Reading)
                         .filter(Reading.id_previous == current.id)
                         .first())
                if not current:
                    break

            books_checked += 1

        return errors

    def test_kindle_backward_chain(self):
        """Test the chain leading up to current Kindle book"""
        current = self._get_current_reading_by_media("kindle")
        errors = self._verify_chain(current, direction="backward")
        self.assertEqual([], errors, f"Kindle backward chain has errors: {errors}")

    def test_hardcover_backward_chain(self):
        """Test the chain leading up to current hardcover book"""
        current = self._get_current_reading_by_media("hardcover")
        errors = self._verify_chain(current, direction="backward")
        self.assertEqual([], errors, f"Hardcover backward chain has errors: {errors}")

    def test_audio_backward_chain(self):
        """Test the chain leading up to current audio book"""
        current = self._get_current_reading_by_media("audio")
        errors = self._verify_chain(current, direction="backward")
        self.assertEqual([], errors, f"Audio backward chain has errors: {errors}")

    def test_kindle_forward_chain(self):
        """Test the chain 20 books past the current Kindle book"""
        current = self._get_current_reading_by_media("kindle")
        errors = self._verify_chain(current, num_books=20, direction="forward")
        self.assertEqual([], errors, f"Kindle forward chain has errors: {errors}")

    def test_hardcover_forward_chain(self):
        """Test the chain 20 books past the current hardcover book"""
        current = self._get_current_reading_by_media("hardcover")
        errors = self._verify_chain(current, num_books=20, direction="forward")
        self.assertEqual([], errors, f"Hardcover forward chain has errors: {errors}")

    def test_audio_forward_chain(self):
        """Test the chain 20 books past the current audio book"""
        current = self._get_current_reading_by_media("audio")
        errors = self._verify_chain(current, num_books=20, direction="forward")
        self.assertEqual([], errors, f"Audio forward chain has errors: {errors}")

if __name__ == '__main__':
    unittest.main()
