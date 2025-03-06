#!/usr/bin/env python3
"""Fix permissions for report files."""
import os
import sys
import grp
from pathlib import Path

def print_error(msg: str) -> None:
    """Print error message in red."""
    print(f"\033[91m{msg}\033[0m")

def print_success(msg: str) -> None:
    """Print success message in green."""
    print(f"\033[92m{msg}\033[0m")

def fix_permissions(reports_dir: Path) -> None:
    """Fix permissions for all report files."""
    try:
        www_data_gid = grp.getgrnam('www-data').gr_gid
        
        # Ensure reports directory is traversable
        reports_dir.chmod(0o755)
        os.chown(str(reports_dir), os.getuid(), www_data_gid)

        # Fix all HTML files
        for html_file in reports_dir.rglob('*.html'):
            html_file.chmod(0o644)
            os.chown(str(html_file), os.getuid(), www_data_gid)
            print_success(f"Fixed permissions for: {html_file}")

    except PermissionError:
        print_error("Error: This script must be run with sudo")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point."""
    # Get project root
    project_root = Path(__file__).resolve().parents[2]
    reports_dir = project_root / 'reports'
    
    if not reports_dir.exists():
        print_error(f"Reports directory not found: {reports_dir}")
        sys.exit(1)

    fix_permissions(reports_dir)
    print_success("All permissions fixed successfully!")

if __name__ == "__main__":
    main()
