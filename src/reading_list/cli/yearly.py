"""CLI command for generating yearly reading reports.

This module provides the command-line interface for generating yearly reading reports.
It handles argument parsing, report generation, and permission management for output files.

Command Usage:
    reading-list yearly <year> [options]

Options:
    --format, -f     Output format (console, html, or both)
    --actual-only    Show only completed readings
    --estimated-only Show only planned/estimated readings
    --verbose, -v    Show detailed error information
"""

import argparse
import traceback
import os
import grp
from pathlib import Path
from rich.console import Console
from ..reports.yearly import generate_report
from ..utils.permissions import fix_report_permissions

console = Console()

def fix_report_permissions(file_path: Path) -> None:
    """Fix permissions for the generated report file.
    
    Ensures the report file and its parent directory have correct permissions
    and ownership for web server access.
    
    Args:
        file_path: Path to the report file
    
    Note:
        - Attempts to set 644 permissions on file
        - Attempts to set 755 permissions on parent directory
        - Attempts to set www-data group ownership
        - Provides guidance if sudo is required
    """
    try:
        # Basic file permissions without sudo
        file_path.chmod(0o644)
        file_path.parent.chmod(0o755)
        
        # Group ownership (requires sudo)
        try:
            www_data_gid = grp.getgrnam('www-data').gr_gid
            os.chown(str(file_path), os.getuid(), www_data_gid)
            os.chown(str(file_path.parent), os.getuid(), www_data_gid)
            console.print("[green]✓ File permissions and ownership fixed[/green]")
        except PermissionError:
            console.print("\n[yellow]Note: Group ownership requires sudo. To fix:[/yellow]")
            console.print(f"[yellow]  sudo chown :www-data {file_path}[/yellow]")
            console.print("[yellow]  # or use the permissions script:[/yellow]")
            console.print("[yellow]  sudo ./scripts/utils/fix_permissions.sh[/yellow]")
            
    except Exception as e:
        pass  # Silently handle other permission errors

def add_subparser(subparsers):
    """Add the yearly command parser to the main parser.
    
    Configures the argument parser for the yearly report command,
    including all available options and help text.
    
    Args:
        subparsers: argparse subparsers object to add to
    
    Returns:
        ArgumentParser: Configured parser for yearly command
    """
    parser = subparsers.add_parser(
        "yearly",
        help="Generate yearly readings report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for a single year
  reading-list yearly 2024

  # Generate reports for multiple years
  reading-list yearly 2021 2022 2023 2024 2025

  # Generate report for actual readings only
  reading-list yearly 2024 --actual-only

  # Generate report for estimated readings only
  reading-list yearly 2024 --estimated-only
        """
    )
    
    parser.add_argument(
        "years",
        type=int,
        nargs='+',
        help="Year(s) to generate report for"
    )
    
    parser.add_argument(
        "--format",
        "-f",
        choices=['console', 'html', 'both'],
        default='both',
        help="Output format (default: both)"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--actual-only",
        action="store_true",
        help="Show only readings with actual start/end dates"
    )
    group.add_argument(
        "--estimated-only",
        action="store_true",
        help="Show only readings with estimated start/end dates"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed error information"
    )
    
    return parser

def handle_command(args):
    """Handle the yearly command."""
    try:
        exit_code = 0
        for year in args.years:
            console.print(f"[blue]Generating yearly reading report for {year}...[/blue]")
            output_file = generate_report(
                year,
                args.format,
                actual_only=args.actual_only,
                estimated_only=args.estimated_only
            )
            if output_file and args.format in ['html', 'both']:
                console.print(f"\n[green]Report generated: {output_file}[/green]")
                fix_report_permissions(Path(output_file))
        return exit_code
    except Exception as e:
        console.print(f"[red]Error generating report: {str(e)}[/red]")
        if args.verbose:
            console.print(f"[red]Traceback:\n{traceback.format_exc()}[/red]")
        return 1
