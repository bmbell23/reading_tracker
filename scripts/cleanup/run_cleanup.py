"""
Project Cleanup Utility

This script runs all cleanup utilities in the correct order to maintain
project cleanliness and data integrity. It performs the following tasks:

1. Test Data Cleanup:
   - Removes test data entries
   - Cleans up test artifacts

2. Database Cleanup:
   - Checks date consistency
   - Removes empty entries
   - Validates relationships

3. Codebase Cleanup:
   - Removes unnecessary __init__.py files
   - Cleans up migration artifacts
   - Consolidates query scripts
   - Removes __pycache__ directories

Usage:
    python run_cleanup.py

Note: This script should be run before committing changes to ensure
      the codebase remains clean and consistent.
"""
from pathlib import Path
import sys
import shutil

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.cleanup.cleanup_test_data import cleanup_test_data
from scripts.cleanup.cleanup_database import check_date_consistency, cleanup_empty_entries
from scripts.cleanup.cleanup_codebase import (
    remove_migration_artifacts,
    consolidate_query_scripts,
    remove_pycache_directories,
)
from scripts.cleanup.fix_permissions import fix_file_permissions

def update_pyproject_toml(project_root: Path):
    """Update pyproject.toml with correct package structure"""
    pyproject_path = project_root / 'pyproject.toml'
    if not pyproject_path.exists():
        print("Warning: pyproject.toml not found")
        return

    with open(pyproject_path, 'r') as f:
        content = f.read()

    # Update package directory settings
    content = content.replace(
        'package-dir = {"" = "."}',
        'package-dir = {"" = "src"}'
    )
    content = content.replace(
        'packages = ["reading_list", "src", "scripts", "tests"]',
        'packages = ["reading_list"]'
    )

    # Backup original file
    backup_path = pyproject_path.with_suffix('.toml.backup')
    shutil.copy2(pyproject_path, backup_path)
    print(f"Backed up original pyproject.toml to {backup_path}")

    # Write updated content
    with open(pyproject_path, 'w') as f:
        f.write(content)
    print("Updated pyproject.toml with new package structure")

def main():
    project_root = Path(__file__).parent.parent.parent

    print("Reading List Project Cleanup Utility")
    print("=" * 40)

    # First organize the root directory
    print("\nStep 1: Organizing project structure...")
    from scripts.cleanup.organize_root import organize_root
    organize_root()

    # Then clean up test data
    print("\nStep 2: Cleaning up test data...")
    cleanup_test_data()

    # Then clean up database
    print("\nStep 3: Cleaning up database...")
    check_date_consistency()
    cleanup_empty_entries()

    # Clean up codebase
    print("\nStep 4: Cleaning up codebase...")
    remove_migration_artifacts(project_root)
    consolidate_query_scripts(project_root)
    remove_pycache_directories(project_root)

    # New: Clean up package structure
    print("\nStep 5: Cleaning up package structure...")
    cleanup_package_structure(project_root)

def cleanup_package_structure(project_root: Path):
    """Ensure consistent package structure"""
    # Move all source files to src/reading_list
    src_dir = project_root / 'src' / 'reading_list'
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # Update pyproject.toml
    update_pyproject_toml(project_root)
    
    # Fix file permissions
    fix_file_permissions(project_root)

if __name__ == "__main__":
    main()
