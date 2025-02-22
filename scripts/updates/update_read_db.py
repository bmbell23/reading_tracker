import argparse
from datetime import date, timedelta
from src.models.base import SessionLocal
from src.models.reading import Reading
from src.models.book import Book
from src.utils.constants import READING_SPEEDS, DEFAULT_WPD

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
            if not reading.date_started and not reading.date_est_start:
                print(f"Skipping reading ID {reading.id} - Missing both actual and estimated start dates")
                self.skipped_count += 1
                continue

            if reading._days_estimate is None:
                # Try to get days_estimate from the property if not set
                reading._days_estimate = reading.days_estimate

            if reading._days_estimate is None:
                print(f"Skipping reading ID {reading.id} - Missing days estimate")
                self.skipped_count += 1
                continue

            # Use actual start date if available, otherwise use estimated start date
            start_date = reading.date_started or reading.date_est_start
            est_end_date = start_date + timedelta(days=reading._days_estimate)
            reading.date_est_end = est_end_date
            self.updates_count += 1

            print(f"Reading ID {reading.id}: {reading.book.title} - {est_end_date.strftime('%Y-%m-%d')}")

        return self.updates_count, self.skipped_count

    def update_chain_dates(self):
        """Calculate and update both est_end and est_start dates for all readings in chain order"""
        print("\nUpdating reading chain dates...")

        readings = self.get_all_readings()
        self.updates_count = 0
        self.skipped_count = 0

        readings_dict = {reading.id: reading for reading in readings}

        for reading in readings:
            if reading._days_estimate is None and reading.days_estimate is not None:
                reading._days_estimate = reading.days_estimate
                print(f"Set days_estimate for ID {reading.id}: {reading.book.title} ({reading._days_estimate} days)")
                self.updates_count += 1

            # Ensure est_start matches actual start date if it exists
            if reading.date_started:
                if reading.date_est_start != reading.date_started:
                    reading.date_est_start = reading.date_started
                    print(f"Aligned est_start with actual start date for ID {reading.id}: {reading.book.title} - {reading.date_started}")
                    self.updates_count += 1

        self.session.commit()

        for media_type in ['kindle', 'hardcover', 'audio']:
            print(f"\nProcessing {media_type} chain...")

            current = (self.session.query(Reading)
                      .filter(Reading.media.ilike(f"%{media_type}%"))
                      .filter(Reading.date_started <= date.today())
                      .filter(Reading.date_finished_actual.is_(None))
                      .first())

            if not current:
                print(f"No current {media_type} reading found")
                continue

            while current:
                if current._days_estimate is not None:
                    # Always use actual start date if available
                    if current.date_started:
                        start_date = current.date_started
                        current.date_est_start = start_date  # Ensure alignment
                    else:
                        start_date = current.date_est_start

                    if start_date:
                        current.date_est_end = start_date + timedelta(days=current._days_estimate)
                        print(f"Set est_end for ID {current.id}: {current.book.title} - {current.date_est_end}")
                        self.updates_count += 1

                next_reading = (self.session.query(Reading)
                              .filter(Reading.id_previous == current.id)
                              .first())

                if not next_reading:
                    break

                if current.date_est_end:
                    if next_reading.date_started:
                        # If next book has started, ensure its est_start matches actual start
                        if next_reading.date_est_start != next_reading.date_started:
                            next_reading.date_est_start = next_reading.date_started
                            print(f"Aligned est_start with actual start date for next ID {next_reading.id}: {next_reading.book.title} - {next_reading.date_started}")
                            self.updates_count += 1
                    else:
                        # Only set est_start if the book hasn't actually started
                        next_reading.date_est_start = current.date_est_end + timedelta(days=1)
                        print(f"Set est_start for next ID {next_reading.id}: {next_reading.book.title} - {next_reading.date_est_start}")
                        self.updates_count += 1

                current = next_reading

            self.session.commit()

        return self.updates_count, self.skipped_count

    def commit_changes(self, updates_count, skipped_count):
        """Commit changes to the database after confirmation"""
        if updates_count > 0:
            confirm = input(f"\nUpdate {updates_count} entries? (Y/n): ").lower()
            if confirm in ['', 'y', 'yes']:  # Empty string (Enter) now counts as yes
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
    parser.add_argument('--est-start', action='store_true', help='Update date_est_start column')
    parser.add_argument('--chain', action='store_true', help='Update both est_end and est_start dates in chain order')

    args = parser.parse_args()

    # If no flags are specified, show usage
    if not any(vars(args).values()):
        parser.print_help()
        return

    try:
        with UpdateReadTable() as updater:
            if args.all or args.chain:
                # First update estimates if needed
                if args.all:
                    updates, skipped = updater.update_days_estimate()
                    updater.commit_changes(updates, skipped)

                # Then update the chain dates
                updates, skipped = updater.update_chain_dates()
                updater.commit_changes(updates, skipped)

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

            if args.all or args.est_start:
                updates, skipped = updater.update_chain_dates()
                updater.commit_changes(updates, skipped)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
