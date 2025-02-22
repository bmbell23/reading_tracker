"""
Main cleanup script that runs all cleanup utilities in the correct order.
"""
from pathlib import Path
from scripts.cleanup.cleanup_test_data import cleanup_test_data
from scripts.cleanup.cleanup_database import check_date_consistency, cleanup_empty_entries
from scripts.cleanup.cleanup_codebase import (
    remove_empty_init_files,
    remove_migration_artifacts,
    consolidate_query_scripts,
    remove_pycache_directories,
    remove_script_init_files
)

def main():
    project_root = Path(__file__).parent.parent.parent

    print("Reading List Project Cleanup Utility")
    print("=" * 40)

    # First clean up test data
    print("\nStep 1: Cleaning up test data...")
    cleanup_test_data()

    # Then clean up database
    print("\nStep 2: Cleaning up database...")
    check_date_consistency()
    cleanup_empty_entries()

    # Finally clean up codebase
    print("\nStep 3: Cleaning up codebase...")
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
