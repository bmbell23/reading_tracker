import os
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Date, or_, and_
from sqlalchemy.orm import declarative_base, sessionmaker

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

def check_date_consistency(project_root: Path):
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

def remove_empty_init_files(project_root: Path):
    """Remove empty __init__.py files"""
    empty_inits = []
    for init_file in project_root.rglob('__init__.py'):
        if init_file.stat().st_size == 0:
            print(f"Found empty __init__.py: {init_file}")
            empty_inits.append(init_file)

    if empty_inits:
        confirm = input("\nRemove these empty __init__.py files? (yes/no): ")
        if confirm.lower() == 'yes':
            for file in empty_inits:
                os.remove(file)
                print(f"Removed: {file}")

def remove_migration_artifacts(project_root: Path):
    """Remove old migration scripts and artifacts"""
    migration_files = [
        'migrate_author_names.py',
        'how_to_git_commit.md',
        'add_days_estimate_column.py',  # Added: old migration script
        'update_days_estimate.py'       # Added: redundant script
    ]

    found_files = []
    for file in migration_files:
        file_path = project_root / 'scripts' / file
        if file_path.exists():
            print(f"Found migration file: {file}")
            found_files.append(file_path)

    if found_files:
        confirm = input("\nRemove these migration files? (yes/no): ")
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

def remove_pycache_directories(project_root: Path):
    """Remove all __pycache__ directories recursively in the scripts folder"""
    scripts_dir = project_root / 'scripts'
    pycache_dirs = list(scripts_dir.rglob('__pycache__'))

    if pycache_dirs:
        print("\nFound __pycache__ directories in scripts:")
        for cache_dir in pycache_dirs:
            print(f"- {cache_dir.relative_to(project_root)}")  # Show path relative to project root

        confirm = input("\nRemove these __pycache__ directories? (Y/n): ").lower()
        if confirm in ['', 'y', 'yes']:
            for cache_dir in pycache_dirs:
                try:
                    for file in cache_dir.iterdir():
                        file.unlink()
                    cache_dir.rmdir()
                    print(f"Removed: {cache_dir.relative_to(project_root)}")
                except Exception as e:
                    print(f"Error removing {cache_dir}: {e}")

def remove_script_init_files(project_root: Path):
    """Remove __init__.py files from scripts directory and its subdirectories"""
    scripts_dir = project_root / 'scripts'
    init_files = list(scripts_dir.rglob('__init__.py'))

    if init_files:
        print("\nFound __init__.py files in scripts directory:")
        for init_file in init_files:
            print(f"- {init_file.relative_to(project_root)}")

        confirm = input("\nRemove these __init__.py files? (Y/n): ").lower()
        if confirm in ['', 'y', 'yes']:
            for init_file in init_files:
                try:
                    init_file.unlink()
                    print(f"Removed: {init_file.relative_to(project_root)}")
                except Exception as e:
                    print(f"Error removing {init_file}: {e}")

def main():
    project_root = Path(__file__).parent.parent

    print("Reading List Project Cleanup Utility")
    print("=" * 40)

    remove_script_init_files(project_root)
    remove_empty_init_files(project_root)
    remove_migration_artifacts(project_root)
    consolidate_query_scripts(project_root)
    remove_pycache_directories(project_root)

    print("\nCleanup complete!")
    print("\nAdditional manual tasks:")
    print("1. Review and update database schema to remove redundant columns")
    print("2. Consider consolidating database query scripts into a single CLI tool")
    print("3. Update documentation to reflect any changes made")
    print("4. Remove src/queries directory if not being used")

if __name__ == "__main__":
    main()
