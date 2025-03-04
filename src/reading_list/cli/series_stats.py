"""CLI command for generating series statistics."""
import argparse
from rich.console import Console
from ..services.series_stats import SeriesStatsService

console = Console()

def add_subparser(subparsers):
    """Add the series-stats command parser to the main parser."""
    parser = subparsers.add_parser(
        "series-stats",
        help="Generate series statistics report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate statistics for all books
  reading-list series-stats

  # Generate statistics for finished books only
  reading-list series-stats --finished-only

  # Generate statistics and save to CSV
  reading-list series-stats --csv
        """
    )
    
    parser.add_argument(
        "--finished-only",
        "-f",
        action="store_true",
        help="Only include books that have been finished reading"
    )
    
    parser.add_argument(
        "--csv",
        "-c",
        action="store_true",
        help="Output results to CSV files"
    )
    
    return parser

def handle_command(args):
    """Handle the series-stats command."""
    try:
        service = SeriesStatsService()
        service.generate_stats(
            finished_only=args.finished_only,
            csv_output=args.csv
        )
        return 0
    except Exception as e:
        console.print(f"[red]Error generating series statistics: {str(e)}[/red]")
        return 1