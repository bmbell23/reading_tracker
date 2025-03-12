"""CLI command for database backup."""
import argparse
from rich.console import Console
from ..database.transfer import DatabaseTransfer

console = Console()

def add_subparser(subparsers):
    """Add the backup-db command parser to the main parser."""
    parser = subparsers.add_parser(
        "backup-db",
        help="Create a backup of the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a database backup
  reading-list backup-db
        """
    )
    return parser

def handle_command(args):
    """Handle the backup-db command."""
    try:
        db_transfer = DatabaseTransfer()
        backup_path = db_transfer.create_backup()  # Use create_backup() instead of export_database()
        return 0
    except Exception as e:
        console.print(f"[red]Error creating database backup: {str(e)}[/red]")
        return 1