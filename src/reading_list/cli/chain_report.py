"""
Reading Chain Report CLI
======================

Command-line interface for generating reading chain reports.
"""

from ..reports.chain_report import generate_chain_report
from rich.console import Console
import argparse

console = Console()

def add_subparser(subparsers):
    """Add the chain-report command parser to the main parser."""
    parser = subparsers.add_parser(
        "chain-report",
        help="Generate reading chain report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate chain report
  reading-list chain-report

  # Generate chain report with custom output path
  reading-list chain-report --output path/to/report.html
        """
    )
    
    parser.add_argument(
        '--output', 
        '-o', 
        help='Output file path',
        default=None
    )
    
    return parser

def handle_command(args):
    """Handle the chain-report command."""
    try:
        generate_chain_report(args)
        return 0
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    exit(main())
