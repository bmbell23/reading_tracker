"""CLI command for generating series statistics."""
import argparse
from rich.console import Console
from ..services.series_stats import SeriesStatsService

console = Console()

def add_subparser(subparsers):
    """Add series-stats command parser"""
    parser = subparsers.add_parser(
        "series-stats",
        help="Generate statistics about series and standalone books"
    )
    parser.add_argument(
        "--finished-only",
        action="store_true",
        help="Only include finished books in statistics"
    )
    parser.add_argument(
        "--upcoming",
        action="store_true",
        help="Show statistics for upcoming books instead of finished books"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also save results to CSV files"
    )
    return parser

def handle_command(args):
    """Handle the series-stats command"""
    service = SeriesStatsService()
    service.generate_stats(
        finished_only=args.finished_only,
        csv_output=args.csv,
        upcoming=args.upcoming
    )
