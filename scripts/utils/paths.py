"""Utility functions for handling project paths."""
from pathlib import Path
import os
from dotenv import load_dotenv

def load_workspace() -> Path:
    """Get the workspace path from environment variables or find it dynamically."""
    # Try to get from environment first
    load_dotenv(os.path.join(find_project_root(), 'config', '.env'))
    workspace = os.getenv('WORKSPACE')

    if workspace:
        return Path(workspace)

    # Fallback to finding it dynamically
    return find_project_root()

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

def get_project_paths():
    """Return a dictionary of common project paths."""
    workspace = load_workspace()

    return {
        'workspace': workspace,
        'config': workspace / 'config',
        'templates': workspace / 'templates',
        'docs': workspace / 'docs',
        'database': workspace / 'data' / 'db' / 'reading_list.db',
        'excel_templates': workspace / 'templates' / 'excel',
        'email_templates': workspace / 'templates' / 'email',
        'migrations': workspace / 'src' / 'migrations',
        'logs': workspace / 'logs',
        'data': workspace / 'data',
        'backups': workspace / 'data' / 'backups',
        'csv': workspace / 'data' / 'csv',
        'examples': workspace / 'data' / 'examples',
    }
