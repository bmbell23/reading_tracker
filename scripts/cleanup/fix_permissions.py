#!/usr/bin/env python3
from pathlib import Path
import sys
import os

def fix_file_permissions(project_root: Path):
    """
    Fix file permissions across the project:
    - Python files: 644 (rw-r--r--)
    - Script entry points: 755 (rwxr-xr-x)
    """
    # Entry point scripts that should be executable
    EXECUTABLE_SCRIPTS = {
        'setup.py',
        'scripts/cleanup/run_cleanup.py',
        'scripts/database/backup_db.py',
        'scripts/database/restore_db.py',
    }
    
    def should_be_executable(file_path: Path) -> bool:
        return any(str(file_path).endswith(script) for script in EXECUTABLE_SCRIPTS)

    # Process all Python files
    for py_file in project_root.rglob("*.py"):
        relative_path = py_file.relative_to(project_root)
        
        # Skip virtual environment
        if "venv" in str(py_file):
            continue
            
        if should_be_executable(relative_path):
            py_file.chmod(0o755)  # rwxr-xr-x
            print(f"Set executable permissions for {relative_path}")
        else:
            py_file.chmod(0o644)  # rw-r--r--
            print(f"Set non-executable permissions for {relative_path}")

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    fix_file_permissions(project_root)