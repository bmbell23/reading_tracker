from pathlib import Path
from sqlalchemy import or_, and_
from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book
from src.models.inventory import Inventory

def check_date_consistency():
    """Check for inconsistencies in reading dates"""
    print("\nChecking reading date consistency...")

    session = SessionLocal()
    try:
        inconsistent_readings = (
            session.query(Reading)
            .filter(
                or_(
                    # est_start doesn't match actual start date when present
                    and_(
                        Reading.date_started.isnot(None),
                        Reading.date_est_start != Reading.date_started
                    ),
                    # est_end before est_start
                    and_(
                        Reading.date_est_start.isnot(None),
                        Reading.date_est_end.isnot(None),
                        Reading.date_est_end < Reading.date_est_start
                    ),
                    # actual end before actual start
                    and_(
                        Reading.date_started.isnot(None),
                        Reading.date_finished_actual.isnot(None),
                        Reading.date_finished_actual < Reading.date_started
                    )
                )
            ).all()
        )

        if inconsistent_readings:
            print("\nFound date inconsistencies:")
            for reading in inconsistent_readings:
                print(f"\nReading ID {reading.id}: {reading.book.title}")
                print(f"  Started: {reading.date_started}")
                print(f"  Est. Start: {reading.date_est_start}")
                print(f"  Est. End: {reading.date_est_end}")
                print(f"  Finished: {reading.date_finished_actual}")

            print("\nRun 'python scripts/updates/update_read_db.py --all' to fix these issues")
        else:
            print("No date inconsistencies found")

    finally:
        session.close()

def cleanup_empty_entries():
    """Remove all entries that have an ID but all other fields are empty/null"""
    session = SessionLocal()
    try:
        # Clean up Books table
        empty_books = session.query(Book).filter(
            Book.title.is_(None),
            Book.author_name_first.is_(None),
            Book.author_name_second.is_(None),
            Book.word_count.is_(None),
            Book.page_count.is_(None),
            Book.date_published.is_(None),
            Book.author_gender.is_(None),
            Book.series.is_(None),
            Book.series_number.is_(None),
            Book.genre.is_(None)
        ).all()

        # Clean up Readings table
        empty_readings = session.query(Reading).filter(
            Reading.id_previous.is_(None),
            Reading.media.is_(None),
            Reading.date_started.is_(None),
            Reading.date_finished_actual.is_(None),
            Reading.rating_horror.is_(None),
            Reading.rating_spice.is_(None),
            Reading.rating_world_building.is_(None),
            Reading.rating_writing.is_(None),
            Reading.rating_characters.is_(None),
            Reading.rating_readability.is_(None),
            Reading.rating_enjoyment.is_(None)
        ).all()

        # Clean up Inventory table
        empty_inventory = session.query(Inventory).filter(
            Inventory.owned_audio.is_(False),
            Inventory.owned_kindle.is_(False),
            Inventory.owned_physical.is_(False),
            Inventory.date_purchased.is_(None),
            Inventory.location.is_(None),
            Inventory.read_status.is_(None),
            Inventory.read_count.is_(None),
            Inventory.isbn_10.is_(None),
            Inventory.isbn_13.is_(None)
        ).all()

        # Print what will be deleted
        print("\nEmpty entries found:")
        print(f"Books: {len(empty_books)}")
        print(f"Readings: {len(empty_readings)}")
        print(f"Inventory: {len(empty_inventory)}")

        if empty_books or empty_readings or empty_inventory:
            confirm = input("\nDo you want to delete these empty entries? (Y/n): ")
            if confirm.lower() in ['', 'y', 'yes']:
                for book in empty_books:
                    session.delete(book)
                for reading in empty_readings:
                    session.delete(reading)
                for inv in empty_inventory:
                    session.delete(inv)

                session.commit()
                print("\nEmpty entries deleted successfully!")
            else:
                print("\nDeletion cancelled")
        else:
            print("\nNo empty entries found")

    except Exception as e:
        print(f"Error: {str(e)}")
        session.rollback()
    finally:
        session.close()

def main():
    print("Reading List Database Cleanup Utility")
    print("=" * 40)

    check_date_consistency()
    cleanup_empty_entries()

if __name__ == "__main__":
    main()
