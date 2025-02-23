#!/usr/bin/env python3
"""
Verify database path and table name consistency across the project.
"""
import os
from pathlib import Path
import re
from typing import List, Tuple

class InconsistencyFinder:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.correct_db_path = "data/db/reading_list.db"
        self.correct_table_name = "read"
        self.excluded_dirs = {'.git', '.venv', 'venv', '__pycache__', 'node_modules'}
        self.issues_found = False

    def check_file_content(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Check file content for incorrect database references."""
        issues = []

        # Skip binary files and specific file types
        if file_path.suffix in {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.db'}:
            return issues

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f.readlines(), 1):
                    # Check for incorrect database paths
                    if 'reading_list.db' in line and 'data/db/' not in line:
                        if not any(exclude in line for exclude in ['data/db', 'backup', 'example']):
                            issues.append((i, line.strip(), "Incorrect database path"))

                    # Check for 'readings' table references
                    if re.search(r'\breadings\b', line, re.IGNORECASE):
                        if not any(exclude in line for exclude in ['rename', 'migration', 'old']):
                            issues.append((i, line.strip(), "Reference to 'readings' table"))

                    # Check for SQLite connection strings
                    if "sqlite:///" in line and self.correct_db_path not in line:
                        if not any(exclude in line for exclude in ['test', 'memory']):
                            issues.append((i, line.strip(), "Incorrect SQLite connection string"))

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

        return issues

    def scan_directory(self):
        """Scan project directory for inconsistencies."""
        print("Scanning project for database path and table name inconsistencies...")
        print("=" * 80)

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]

            for file in files:
                file_path = Path(root) / file
                issues = self.check_file_content(file_path)

                if issues:
                    self.issues_found = True
                    print(f"\nFile: {file_path.relative_to(self.project_root)}")
                    for line_num, line, issue_type in issues:
                        print(f"  Line {line_num}: {issue_type}")
                        print(f"    {line}")

    def verify_database_schema(self):
        """Verify the actual database schema."""
        try:
            from sqlalchemy import create_engine, inspect

            db_path = self.project_root / self.correct_db_path
            if not db_path.exists():
                print(f"\nWarning: Database file not found at {db_path}")
                return

            engine = create_engine(f'sqlite:///{db_path}')
            inspector = inspect(engine)

            if 'readings' in inspector.get_table_names():
                self.issues_found = True
                print("\nDatabase Schema Issue: 'readings' table still exists!")
                print("Run the table rename migration script to fix this.")

        except Exception as e:
            print(f"\nError checking database schema: {e}")

def main():
    project_root = Path(__file__).parent.parent
    finder = InconsistencyFinder(project_root)

    finder.scan_directory()
    finder.verify_database_schema()

    print("\n" + "=" * 80)
    if finder.issues_found:
        print("Issues found! Please review and fix the above inconsistencies.")
        print("\nCommon fixes:")
        print("1. Update database paths to use 'data/db/reading_list.db'")
        print("2. Replace 'readings' table references with 'read'")
        print("3. Run database migrations if needed")
        exit(1)
    else:
        print("No inconsistencies found!")

if __name__ == "__main__":
    main()