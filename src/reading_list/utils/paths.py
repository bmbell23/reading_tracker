"""Utility functions for handling project paths."""
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Dict

def find_project_root(start_path: Path = None) -> Path:
    """Find the project root directory by looking for .project-root marker file."""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.absolute()

    while current != current.parent:
        if (current / '.project-root').exists():
            return current
        current = current.parent

    raise FileNotFoundError(
        "Project root not found. Ensure .project-root file exists in project root directory."
    )

def load_workspace() -> Path:
    """Get the workspace path from environment variables or find it dynamically."""
    # Try to get from environment first
    load_dotenv(os.path.join(find_project_root(), 'config', '.env'))
    workspace = os.getenv('WORKSPACE')

    if workspace:
        return Path(workspace)

    # Fallback to finding it dynamically
    return find_project_root()

def get_project_paths() -> Dict[str, Path]:
    """Get standardized paths for the project."""
    # Get the project root (3 levels up from this file)
    root = Path(__file__).resolve().parents[3]
    
    return {
        'root': root,
        'src': root / 'src',
        'templates': root / 'src' / 'reading_list' / 'templates',
        'reports': root / 'reports',
        'assets': root / 'assets',
        'workspace': root,
        'database': root / 'data' / 'db' / 'reading_list.db',
        'backups': root / 'data' / 'db' / 'backups'  # Updated path
    }

def ensure_paths_exist():
    """Ensure all required project paths exist."""
    paths = get_project_paths()
    
    # Create directories if they don't exist
    for path in paths.values():
        # Skip database file itself, just create its parent directory
        if str(path).endswith('.db'):
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)
        
    # Create specific report subdirectories
    report_types = ['yearly', 'monthly', 'projected', 'chain']
    for report_type in report_types:
        (paths['reports'] / report_type).mkdir(parents=True, exist_ok=True)

def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)

def ensure_project_directories() -> Dict[str, Path]:
    """Ensure all required project directories exist."""
    paths = get_project_paths()
    
    # Ensure each directory exists
    for path in paths.values():
        if not path.suffix:  # Only create if it's a directory (no file extension)
            ensure_directory(path)
    
    return paths

def setup_python_path() -> None:
    """Add project root to Python path."""
    import sys
    project_root = find_project_root()
    sys.path.insert(0, str(project_root))
