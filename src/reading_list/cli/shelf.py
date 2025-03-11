"""CLI command for displaying physical books by shelf."""
import argparse
from rich.console import Console
from ..services.shelf_display import ShelfDisplayService

console = Console()

def add_subparser(subparsers):
    """Add the shelf command parser to the main parser."""
    parser = subparsers.add_parser(
        "shelf",
        help="Display physical books organized by shelf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all physical books organized by shelf
  reading-list shelf
  
  # Show only the count of books per shelf
  reading-list shelf --count
  
  # Show books and prompt to shelve any unshelved books
  reading-list shelf --shelve
        """
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Show only the count of books per shelf"
    )
    parser.add_argument(
        "--shelve",
        action="store_true",
        help="Prompt to shelve any unshelved books"
    )
    return parser

def handle_command(args):
    """Handle the shelf command."""
    try:
        service = ShelfDisplayService()
        service.display_books(
            show_count_only=args.count,
            prompt_unshelved=args.shelve
        )
        return 0
    except Exception as e:
        console.print(f"[red]Error displaying shelf contents: {str(e)}[/red]")
        return 1