"""CLI command for generating media statistics."""
import argparse
from rich.console import Console
from ..services.media_stats import MediaStatsService

console = Console()

def add_subparser(subparsers):
    """Add the media-stats command parser to the main parser."""
    parser = subparsers.add_parser(
        "media-stats",
        help="Generate media statistics report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate statistics for all books
  reading-list media-stats

  # Generate statistics for finished books only
  reading-list media-stats --finished-only

  # Generate statistics and save to CSV
  reading-list media-stats --csv
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
        help="Output results to CSV file"
    )
    
    return parser

def handle_command(args):
    """Handle the media-stats command."""
    try:
        service = MediaStatsService()
        service.generate_stats(
            finished_only=args.finished_only,
            csv_output=args.csv
        )
        return 0
    except Exception as e:
        console.print(f"[red]Error generating media statistics: {str(e)}[/red]")
        return 1
