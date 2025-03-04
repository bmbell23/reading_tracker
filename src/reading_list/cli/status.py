"""CLI command for displaying reading status."""
import argparse
from ..services.status_display import StatusDisplay

def add_subparser(subparsers):
    """Add the status command parser to the main parser."""
    parser = subparsers.add_parser(
        "status",
        help="Show current and upcoming reading status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all status tables
  reading-list status

  # Show only current readings
  reading-list status --current-only

  # Show only upcoming readings
  reading-list status --upcoming-only

  # Show only forecast
  reading-list status --forecast-only
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--current-only",
        action="store_true",
        help="Show only current readings"
    )
    group.add_argument(
        "--upcoming-only",
        action="store_true",
        help="Show only upcoming readings"
    )
    group.add_argument(
        "--forecast-only",
        action="store_true",
        help="Show only reading forecast"
    )
    
    return parser

def handle_command(args):
    """Handle the status command."""
    status = StatusDisplay()
    
    if args.current_only:
        status.show_current_readings()
    elif args.upcoming_only:
        status.show_upcoming_readings()
    elif args.forecast_only:
        status.show_progress_forecast()
    else:
        status.show_current_readings()
        status.show_upcoming_readings()
        status.show_progress_forecast()
    
    return 0
