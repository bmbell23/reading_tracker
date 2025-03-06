"""CLI command for generating yearly reading reports."""
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
    """Fix permissions for the generated report file."""
    try:
        # First try to set basic file permissions without sudo
        file_path.chmod(0o644)
        file_path.parent.chmod(0o755)
        
        # Then try to set group ownership (requires sudo)
        try:
            www_data_gid = grp.getgrnam('www-data').gr_gid
            os.chown(str(file_path), os.getuid(), www_data_gid)
            os.chown(str(file_path.parent), os.getuid(), www_data_gid)
            console.print("[green]✓ File permissions and ownership fixed[/green]")
        except PermissionError:
            console.print("\n[yellow]Note: Group ownership requires sudo. To fix, run:[/yellow]")
            console.print(f"[yellow]  sudo chown :www-data {file_path}[/yellow]")
            console.print("[yellow]  # or use the permissions script:[/yellow]")
            console.print("[yellow]  sudo ./scripts/utils/fix_permissions.sh[/yellow]")
            
    except Exception as e:
        pass  # Silently handle other permission errors as they'll be caught by the PermissionError above

def add_subparser(subparsers):
    """Add the yearly command parser to the main parser."""
    parser = subparsers.add_parser(
        "yearly",
        help="Generate yearly readings report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for any year (shows both actual and estimated readings)
  reading-list yearly 2024

  # Generate report for actual readings only
  reading-list yearly 2024 --actual-only

  # Generate report for estimated readings only
  reading-list yearly 2024 --estimated-only
        """
    )
    
    parser.add_argument(
        "year",
        type=int,
        help="Year to generate report for"
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
        console.print("[blue]Generating yearly reading report...[/blue]")
        output_file = generate_report(
            args.year,
            args.format,
            actual_only=args.actual_only,
            estimated_only=args.estimated_only
        )
        if output_file and args.format in ['html', 'both']:
            console.print(f"\n[green]Report generated: {output_file}[/green]")
            fix_report_permissions(Path(output_file))
        return 0
    except Exception as e:
        console.print(f"[red]Error generating report: {str(e)}[/red]")
        if args.verbose:
            console.print(f"[red]Traceback:\n{traceback.format_exc()}[/red]")
        return 1
