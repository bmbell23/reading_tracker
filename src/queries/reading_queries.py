from datetime import date
from sqlalchemy import select
from ..models.base import SessionLocal
from ..models.book import Book
from ..models.reading import Reading

class ReadingQueries:
    def __init__(self):
        self.session = SessionLocal()

    def __del__(self):
        """Ensure the session is closed when the object is destroyed"""
        self.session.close()

    def get_current_unfinished_readings(self):
        """
        Get all books that have been started but not finished yet.
        Returns: List of tuples (title, author, date_started, media)
        """
        try:
            query = (
                select(Book.title, Book.author, Reading.date_started, Reading.media)
                .join(Book, Reading.book_id == Book.id)
                .where(Reading.date_started <= date.today())
                .where(Reading.date_finished_actual.is_(None))
                .order_by(Reading.date_started.desc())
            )

            return self.session.execute(query).all()

        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    def get_readings_started_in_year(self, year: int):
        """
        Get all readings started in a specific year.
        Args:
            year: The year to query for
        Returns: List of tuples (book_id, title, author, date_started, date_finished_actual)
        """
        try:
            query = (
                select(
                    Reading.book_id,
                    Book.title,
                    Book.author,
                    Reading.date_started,
                    Reading.date_finished_actual
                )
                .join(Book, Reading.book_id == Book.id)
                .where(Reading.date_started >= f"{year}-01-01")
                .where(Reading.date_started < f"{year+1}-01-01")
                .order_by(Reading.date_started.desc())
            )

            return self.session.execute(query).all()

        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    @staticmethod
    def format_reading_results(results, include_finished=False):
        """
        Format the results into a readable string
        Args:
            results: Query results to format
            include_finished: Whether to include finished date in output
        """
        if not results:
            return "No books found."

        output = "Books:\n"
        for result in results:
            if include_finished and len(result) >= 5:  # If we have finished date
                book_id, title, author, start_date, finish_date = result
                finished_str = f", finished: {finish_date}" if finish_date else " (unfinished)"
                output += f"- {title} by {author} (started: {start_date}{finished_str})\n"
            else:
                book_id, title, author, start_date = result[:4]
                output += f"- {title} by {author} (started: {start_date})\n"
        return output

if __name__ == "__main__":
    # Example usage
    queries = ReadingQueries()
    results = queries.get_current_unfinished_readings()
    print(ReadingQueries.format_reading_results(results))
