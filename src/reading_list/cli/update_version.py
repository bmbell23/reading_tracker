#!/usr/bin/env python3
"""
Version Update Utility
=====================

Updates version numbers across project files.
"""

import sys
import re
from pathlib import Path
import argparse
from rich.console import Console
from ..utils.paths import find_project_root

console = Console()

def get_version_from_file(file_path: Path) -> str:
    """Extract version number from a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

        # Different patterns for different file types
        patterns = {
            'pyproject.toml': r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'README.md': r'# Reading List Tracker v([\d.]+)'
        }

        pattern = patterns.get(file_path.name)
        if pattern:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
    return None

def check_versions() -> dict:
    """Check versions across all project files and return results."""
    project_root = find_project_root()

    files_to_check = {
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
    console.print("\n[bold]Current Version Status:[/bold]")
    console.print("─" * 50)

    # Find the most common version (excluding None values)
    all_versions = [v for v in versions.values() if v is not None]
    if not all_versions:
        console.print("[red]No version information found![/red]")
        return

    main_version = max(set(all_versions), key=all_versions.count)

    # Print status for each file
    has_mismatch = False
    for file, version in versions.items():
        if version is None:
            status = "[red]❌ No version found[/red]"
            has_mismatch = True
        elif version != main_version:
            status = f"[red]❌ Mismatch: {version}[/red]"
            has_mismatch = True
        else:
            status = f"[green]✓ {version}[/green]"

        console.print(f"{file:<15} {status}")

    console.print("─" * 50)
    if has_mismatch:
        console.print("[yellow]⚠️  Version mismatch detected! Use --update to set a new version.[/yellow]")
    else:
        console.print(f"[green]✓ All files are at version {main_version}[/green]")

def update_version(new_version: str):
    """Update version number across all relevant project files."""
    project_root = find_project_root()

    console.print(f"\n[bold]Updating project version to {new_version}[/bold]")
    console.print("─" * 50)

    # Update pyproject.toml
    pyproject_path = project_root / 'pyproject.toml'
    if pyproject_path.exists():
        try:
            update_pyproject_toml(pyproject_path, new_version)
            console.print("[green]✓ Updated pyproject.toml[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to update pyproject.toml: {str(e)}[/red]")

    # Update README.md
    readme_path = project_root / 'README.md'
    if readme_path.exists():
        try:
            update_readme_md(readme_path, new_version)
            console.print("[green]✓ Updated README.md[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to update README.md: {str(e)}[/red]")

    console.print("─" * 50)
    console.print("[green]Version update complete![/green]")

def update_pyproject_toml(file_path: Path, new_version: str):
    """Update version in pyproject.toml"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

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

def main(args=None):
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Update or check project version')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--update', help='Update to specified version')
    group.add_argument('--check', action='store_true', help='Check current version')

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    if args.check:
        versions = check_versions()
        print_version_status(versions)
    elif args.update:
        if not validate_version(args.update):
            console.print(f"[red]Error: Invalid version format: {args.update}[/red]")
            console.print("Version must be in format: X.Y.Z (e.g., 1.0.0)")
            return 1
        update_version(args.update)

    return 0

if __name__ == "__main__":
    sys.exit(main())
