import sys
import os
import re
from pathlib import Path

def update_version(new_version: str):
    """Update version number across all relevant project files."""

    # Get project root directory (two levels up from this script)
    project_root = Path(__file__).parent.parent

    # File patterns and their update functions
    files_to_update = {
        'setup.py': update_setup_py,
        'pyproject.toml': update_pyproject_toml,
        'README.md': update_readme_md
    }

    print(f"\nUpdating project version to {new_version}")
    print("-" * 50)

    # Process each file
    for filename, update_func in files_to_update.items():
        file_path = project_root / filename
        if file_path.exists():
            try:
                update_func(file_path, new_version)
                print(f"✓ Updated {filename}")
            except Exception as e:
                print(f"✗ Failed to update {filename}: {str(e)}")
        else:
            print(f"✗ File not found: {filename}")

    print("-" * 50)
    print("Version update complete!")

def update_setup_py(file_path: Path, new_version: str):
    """Update version in setup.py"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Update version in setup() call
    updated = re.sub(
        r'(version\s*=\s*["\'])[\d.]+(["\'])',
        f'\\g<1>{new_version}\\g<2>',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated)

def update_pyproject_toml(file_path: Path, new_version: str):
    """Update version in pyproject.toml"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Update version in [project] section
    updated = re.sub(
        r'(version\s*=\s*["\'])[\d.]+(["\'])',
        f'\\g<1>{new_version}\\g<2>',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated)

def update_readme_md(file_path: Path, new_version: str):
    """Update version in README.md"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Update version in title
    updated = re.sub(
        r'(# Reading List Tracker v)[\d.]+',
        f'\\g<1>{new_version}',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated)

def validate_version(version: str) -> bool:
    """Validate version number format (e.g., 1.0.0)"""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))

def main():
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        print("Example: python update_version.py 1.1.0")
        sys.exit(1)

    new_version = sys.argv[1]

    if not validate_version(new_version):
        print("Error: Version must be in format X.Y.Z (e.g., 1.0.0)")
        sys.exit(1)

    update_version(new_version)

if __name__ == "__main__":
    main()