import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book
from src.utils.constants import READING_SPEEDS, DEFAULT_WPD
from datetime import timedelta

class UpdateReadTable:
    def __init__(self):
        self.session = SessionLocal()
        self.updates_count = 0
        self.skipped_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_all_readings(self):
        """Get all readings joined with their books"""
        return self.session.query(Reading).join(Book).all()

    def update_days_estimate(self):
        """Calculate and update days_estimate for all reading entries"""
        print("\nCalculating days estimates...")

        readings = self.get_all_readings()
        self.updates_count = 0
        self.skipped_count = 0

        for reading in readings:
            if not reading.book.word_count or not reading.media:
                print(f"Skipping reading ID {reading.id} - Missing word count or media type")
                self.skipped_count += 1
                continue

            media_lower = reading.media.lower()
            words_per_day = READING_SPEEDS.get(media_lower, DEFAULT_WPD)
            days_estimate = int(reading.book.word_count / words_per_day)

            reading._days_estimate = days_estimate
            self.updates_count += 1

            print(f"Reading ID {reading.id}: {reading.book.title} - {days_estimate} days")

        return self.updates_count, self.skipped_count

    def update_days_elapsed(self):
        """Calculate and update days_elapsed_to_read for all reading entries"""
        print("\nCalculating days elapsed...")

        readings = self.get_all_readings()
        self.updates_count = 0
        self.skipped_count = 0

        for reading in readings:
            if not reading.date_started or not reading.date_finished_actual:
                print(f"Skipping reading ID {reading.id} - Missing start or finish date")
                self.skipped_count += 1
                continue

            # Add 1 to include both start and end dates in the count
            days_elapsed = (reading.date_finished_actual - reading.date_started).days + 1
            reading._days_elapsed_to_read = days_elapsed
            self.updates_count += 1

            print(f"Reading ID {reading.id}: {reading.book.title} - {days_elapsed} days")

        return self.updates_count, self.skipped_count

    def update_days_delta(self):
        """Calculate and update days_to_read_delta_from_estimate for all reading entries"""
        print("\nCalculating days delta...")

        readings = self.get_all_readings()
        self.updates_count = 0
        self.skipped_count = 0

        for reading in readings:
            if reading._days_estimate is None or reading._days_elapsed_to_read is None:
                print(f"Skipping reading ID {reading.id} - Missing estimate or elapsed days")
                self.skipped_count += 1
                continue

            days_delta = reading._days_elapsed_to_read - reading._days_estimate
            reading._days_to_read_delta_from_estimate = days_delta
            self.updates_count += 1

            print(f"Reading ID {reading.id}: {reading.book.title} - {days_delta} days difference")

        return self.updates_count, self.skipped_count

    def update_est_end_date(self):
        """Calculate and update date_est_end for all reading entries"""
        print("\nCalculating estimated end dates...")

        readings = self.get_all_readings()
        self.updates_count = 0
        self.skipped_count = 0

        for reading in readings:
            if not reading.date_started or reading._days_estimate is None:
                print(f"Skipping reading ID {reading.id} - Missing start date or days estimate")
                self.skipped_count += 1
                continue

            est_end_date = reading.date_started + timedelta(days=reading._days_estimate)
            reading.date_est_end = est_end_date
            self.updates_count += 1

            print(f"Reading ID {reading.id}: {reading.book.title} - {est_end_date.strftime('%Y-%m-%d')}")

        return self.updates_count, self.skipped_count

    def commit_changes(self, updates_count, skipped_count):
        """Commit changes to the database after confirmation"""
        if updates_count > 0:
            confirm = input(f"\nUpdate {updates_count} entries? (yes/no): ")
            if confirm.lower() == 'yes':
                self.session.commit()
                print(f"\nSuccessfully updated {updates_count} entries!")
                if skipped_count > 0:
                    print(f"Skipped {skipped_count} entries due to missing data")
            else:
                print("\nUpdate cancelled")
                self.session.rollback()
        else:
            print("\nNo entries to update")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Update read table calculations')
    parser.add_argument('--all', action='store_true', help='Update all calculated columns')
    parser.add_argument('--estimate', action='store_true', help='Update days_estimate column')
    parser.add_argument('--elapsed', action='store_true', help='Update days_elapsed_to_read column')
    parser.add_argument('--delta', action='store_true', help='Update days_to_read_delta_from_estimate column')
    parser.add_argument('--est-end', action='store_true', help='Update date_est_end column')

    args = parser.parse_args()

    # If no flags are specified, show usage
    if not any(vars(args).values()):
        parser.print_help()
        return

    try:
        with UpdateReadTable() as updater:
            if args.all or args.estimate:
                updates, skipped = updater.update_days_estimate()
                updater.commit_changes(updates, skipped)

            if args.all or args.elapsed:
                updates, skipped = updater.update_days_elapsed()
                updater.commit_changes(updates, skipped)

            if args.all or args.delta:
                updates, skipped = updater.update_days_delta()
                updater.commit_changes(updates, skipped)

            if args.all or args.est_end:
                updates, skipped = updater.update_est_end_date()
                updater.commit_changes(updates, skipped)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
