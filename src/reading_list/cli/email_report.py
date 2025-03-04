"""CLI command for sending email reading reports."""
import argparse
from ..services.email_report import EmailReport

def add_subparser(subparsers):
    """Add the email-report command parser to the main parser."""
    parser = subparsers.add_parser(
        "email-report",
        help="Send reading status report via email",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send reading status report
  reading-list email-report
        """
    )
    return parser

def handle_command(args):
    """Handle the email-report command."""
    report = EmailReport()
    success = report.send_reading_status()
    return 0 if success else 1