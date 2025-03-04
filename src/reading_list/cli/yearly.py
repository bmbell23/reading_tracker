"""CLI command for generating yearly reading reports."""
import argparse
import traceback
from rich.console import Console
from ..reports.yearly import generate_report

console = Console()

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
        output_file = generate_report(
            args.year,
            args.format,
            actual_only=args.actual_only,
            estimated_only=args.estimated_only
        )
        if output_file and args.format in ['html', 'both']:
            console.print(f"\n[green]Report saved to: {output_file}[/green]")
        return 0
    except Exception as e:
        console.print(f"[red]Error generating report: {str(e)}[/red]")
        if args.verbose:
            console.print(f"[red]Traceback:\n{traceback.format_exc()}[/red]")
        return 1
