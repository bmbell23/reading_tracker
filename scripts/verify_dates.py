import sys
import sys
from datetime import timedelta
from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book

def verify_reading_chain(reading_id):
    session = SessionLocal()
    try:
        # Get the initial reading
        reading = session.get(Reading, reading_id)
        if not reading:
            print(f"No reading found with ID {reading_id}")
            return

        # First, go backwards to find the start of the chain
        chain = []
        current = reading
        while current:
            chain.insert(0, current)  # Add to start of list
            if not current.id_previous:
                break
            current = session.get(Reading, current.id_previous)

        # Now print the chain in order
        print("\nReading Chain:")
        print("-" * 50)
        for i, entry in enumerate(chain):
            print(f"\nPosition {i+1}:")
            print(f"Reading ID: {entry.id}")
            print(f"Title: {entry.book.title}")
            print(f"Start Date: {entry.date_started}")
            print(f"Est Start: {entry.date_est_start}")
            print(f"Est End: {entry.date_est_end}")

            if entry.id_previous:
                prev = session.get(Reading, entry.id_previous)
                if prev:
                    print(f"Previous reading ID: {prev.id}")
                    print(f"Previous Est End: {prev.date_est_end}")

                    if prev.date_est_end:
                        expected_start = prev.date_est_end + timedelta(days=1)
                        if not entry.date_est_start:
                            print(f"ERROR: Missing est_start date. Should be {expected_start}")
                        elif entry.date_est_start != expected_start:
                            print(f"ERROR: Est start date should be {expected_start} (day after previous book ends)")
                else:
                    print(f"Warning: Previous reading (ID: {entry.id_previous}) not found")

            # Check for subsequent reading
            next_reading = session.query(Reading).filter(Reading.id_previous == entry.id).first()
            if next_reading:
                print(f"Next reading ID: {next_reading.id}")
                print(f"Next Est Start: {next_reading.date_est_start}")
                if entry.date_est_end:
                    expected_next_start = entry.date_est_end + timedelta(days=1)
                    if not next_reading.date_est_start:
                        print(f"ERROR: Next book missing est_start date. Should be {expected_next_start}")
                    elif next_reading.date_est_start != expected_next_start:
                        print(f"ERROR: Next book should start {expected_next_start} (day after this book ends)")

    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_dates.py <reading_id>")
        sys.exit(1)
    verify_reading_chain(int(sys.argv[1]))
