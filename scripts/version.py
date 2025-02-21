import sys
import os
import re
from pathlib import Path
import argparse

def get_version_from_file(file_path: Path) -> str:
    """Extract version number from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

        # Different patterns for different file types
        patterns = {
            'setup.py': r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'pyproject.toml': r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'README.md': r'# Reading List Tracker v(\d+\.\d+\.\d+)'
        }

        pattern = patterns.get(file_path.name)
        if pattern:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
    return None

def check_versions() -> dict:
    """Check versions across all project files and return results."""
    project_root = Path(__file__).parent.parent

    files_to_check = {
        'setup.py': project_root / 'setup.py',
        'pyproject.toml': project_root / 'pyproject.toml',
        'README.md': project_root / 'README.md'
    }

    versions = {}
    for name, path in files_to_check.items():
        if path.exists():
            version = get_version_from_file(path)
            versions[name] = version

    return versions

def print_version_status(versions: dict):
    """Print current version status and highlight any mismatches."""
    print("\nCurrent Version Status:")
    print("-" * 50)

    # Find the most common version
    all_versions = [v for v in versions.values() if v is not None]
    if not all_versions:
        print("No version information found!")
        return

    main_version = max(set(all_versions), key=all_versions.count)

    # Print status for each file
    has_mismatch = False
    for file, version in versions.items():
        if version is None:
            status = "❌ No version found"
        elif version != main_version:
            status = f"❌ Mismatch: {version}"
            has_mismatch = True
        else:
            status = f"✓ {version}"

        print(f"{file:<15} {status}")

    print("-" * 50)
    if has_mismatch:
        print("⚠️  Version mismatch detected! Use --update to set a new version.")
    else:
        print(f"✓ All files are at version {main_version}")

def version(new_version: str):
    """Update version number across all relevant project files."""
    project_root = Path(__file__).parent.parent

    files_to_update = {
        'setup.py': update_setup_py,
        'pyproject.toml': update_pyproject_toml,
        'README.md': update_readme_md
    }

    print(f"\nUpdating project version to {new_version}")
    print("-" * 50)

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
    parser = argparse.ArgumentParser(description='Check or update project version')
    parser.add_argument('--update', help='Update to new version (e.g., 1.1.0)')

    args = parser.parse_args()

    if args.update:
        if not validate_version(args.update):
            print("Error: Version must be in format X.Y.Z (e.g., 1.0.0)")
            sys.exit(1)
        version(args.update)
    else:
        versions = check_versions()
        print_version_status(versions)

if __name__ == "__main__":
    main()
