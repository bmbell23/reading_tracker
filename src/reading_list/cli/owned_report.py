"""CLI command for generating owned books report."""
import argparse
from rich.console import Console
from ..reports.owned_books_report import OwnedBooksReport  # Updated import path

console = Console()

def handle_command(args):
    """Handle the owned-report command."""
    try:
        report = OwnedBooksReport()
        output_path, success = report.generate_report()
        
        if success:
            console.print(f"[green]Report generated successfully at: {output_path}[/green]")
            return 0
        else:
            console.print(f"[red]{output_path}[/red]")
            return 1
    except Exception as e:
        console.print(f"[red]Error generating report: {str(e)}[/red]")
        return 1

def add_subparser(subparsers):
    """Add the owned-report command parser to the main parser."""
    parser = subparsers.add_parser(
        "owned-report",
        help="Generate an HTML report of all owned books",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate owned books report
  reading-list owned-report
        """
    )
    return parser