from pathlib import Path

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
