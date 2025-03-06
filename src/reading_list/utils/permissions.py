"""Utilities for handling file permissions."""
import os
import grp
from pathlib import Path
from rich.console import Console

console = Console()

def fix_report_permissions(file_path: Path) -> None:
    """Fix permissions for the generated report file."""
    try:
        # Ensure parent directory has correct permissions first
        parent_dir = file_path.parent
        try:
            parent_dir.chmod(0o755)
        except PermissionError:
            console.print("[yellow]Need sudo to fix directory permissions[/yellow]")
            
        # Fix file permissions
        if file_path.exists():
            try:
                file_path.chmod(0o644)
            except PermissionError:
                console.print("[yellow]Need sudo to fix file permissions[/yellow]")
        
        # Try to set group ownership
        try:
            www_data_gid = grp.getgrnam('www-data').gr_gid
            os.chown(str(parent_dir), os.getuid(), www_data_gid)
            if file_path.exists():
                os.chown(str(file_path), os.getuid(), www_data_gid)
            console.print("[green]✓ File permissions and ownership fixed[/green]")
        except PermissionError:
            console.print("\n[yellow]To fix permissions completely, run:[/yellow]")
            console.print("[yellow]sudo ./scripts/utils/fix_permissions.sh[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not set group ownership: {str(e)}[/yellow]")
            
    except Exception as e:
        console.print(f"[yellow]Warning: Permission operation failed: {str(e)}[/yellow]")
