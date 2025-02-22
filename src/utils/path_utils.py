from pathlib import Path
from typing import Optional

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent

def get_database_path() -> Path:
    """Get the database file path."""
    root = get_project_root()
    return root / "data" / "db" / "reading_list.db"

def get_backup_path() -> Path:
    """Get the database backup directory path."""
    root = get_project_root()
    return root / "data" / "backups"

def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)
