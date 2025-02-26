import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Date, or_, and_
from sqlalchemy.orm import declarative_base, sessionmaker
import argparse

Base = declarative_base()

class Reading(Base):
    __tablename__ = 'read'  # Changed from 'readings'
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, nullable=False)
    date_started = Column(Date)
    date_est_start = Column(Date)
    date_est_end = Column(Date)
    date_finished_actual = Column(Date)

# Create an engine and bind it to the Base
engine = create_engine('sqlite:///data/db/reading_list.db')
Base.metadata.create_all(engine)

# Create a session
SessionLocal = sessionmaker(bind=engine)

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

def remove_migration_artifacts(project_root: Path, dry_run: bool = False):
    """Remove old migration scripts and artifacts"""
    # Files in scripts/migrations directory
    migration_files = [
        ('scripts/migrations', 'migrate_author_names.py'),
        ('scripts/migrations', 'how_to_git_commit.md'),
        ('scripts/migrations', 'add_days_estimate_column.py'),
        ('scripts/migrations', 'update_days_estimate.py'),
    ]

    found_files = []

    # Check migration files
    for directory, file in migration_files:
        file_path = project_root / directory / file
        if file_path.exists():
            print(f"Found migration file: {file}")
            found_files.append(file_path)

    if found_files:
        if dry_run:
            print("\nDry run - no files will be removed")
        else:
            confirm = input("\nRemove these files? (yes/no): ")
            if confirm.lower() == 'yes':
                for file in found_files:
                    os.remove(file)
                    print(f"Removed: {file}")

def consolidate_query_scripts(project_root: Path):
    """Print information about query scripts that could be consolidated"""
    query_scripts = [
        'query_db.py',
        'show_current_readings.py'
    ]

    found_scripts = []
    for script in query_scripts:
        script_path = project_root / 'scripts' / script
        if script_path.exists():
            found_scripts.append(script)

    if found_scripts:
        print("\nConsider consolidating these query scripts:")
        for script in found_scripts:
            print(f"- {script}")
        print("\nSuggestion: Create a unified CLI tool for database queries")
        print("Example structure:")
        print("  query_db.py --current-readings")
        print("  query_db.py --cleanup-books")
        print("  query_db.py --cleanup-empty")

def remove_pycache_directories(project_root: Path, dry_run: bool = False):
    """Remove all __pycache__ directories recursively in the project"""
    pycache_dirs = list(project_root.rglob('__pycache__'))

    if pycache_dirs:
        pycache_count = len(pycache_dirs)
        print(f"\nFound {pycache_count} __pycache__ directories")
        for cache_dir in pycache_dirs:
            try:
                for file in cache_dir.iterdir():
                    file.unlink()
                cache_dir.rmdir()
            except Exception as e:
                print(f"Error removing {cache_dir}: {e}")
        print(f"All {pycache_count} __pycache__ directories removed successfully!")

def main():
    parser = argparse.ArgumentParser(description="Cleanup codebase utility")
    parser.add_argument('--check', action='store_true',
                       help='Run in check mode without making changes')
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    print("Reading List Project Cleanup Utility")
    print("=" * 40)

    if args.check:
        print("Running in check mode - no changes will be made")

    check_date_consistency()
    remove_migration_artifacts(project_root, dry_run=args.check)
    consolidate_query_scripts(project_root)
    remove_pycache_directories(project_root, dry_run=args.check)

    if args.check:
        print("\nCheck complete - no changes were made")
    else:
        print("\nCleanup complete!")

if __name__ == "__main__":
    main()
