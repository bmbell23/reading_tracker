"""CLI command for fetching book covers from Google Images."""
import argparse
from rich.console import Console
from ..models.base import SessionLocal  # Change this import
from ..services.image_fetcher import download_book_cover

console = Console()

def add_subparser(subparsers):
    """Add the fetch-cover command parser to the main parser."""
    parser = subparsers.add_parser(
        "fetch-cover",
        help="Fetch book cover from Google Images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch cover for a single book
  reading-list fetch-cover 123

  # Fetch covers for multiple books
  reading-list fetch-cover 123 456 789
        """
    )
    
    parser.add_argument(
        "book_ids",
        type=int,
        nargs="+",
        help="Book ID(s) to fetch covers for"
    )
    
    return parser

def handle_command(args):
    """Handle the fetch-cover command."""
    try:
        with SessionLocal() as session:  # Use SessionLocal directly
            success_count = 0
            for book_id in args.book_ids:
                if download_book_cover(session, book_id):
                    success_count += 1
            
            total = len(args.book_ids)
            if success_count == total:
                console.print(f"[green]Successfully fetched all {total} covers![/green]")
                return 0
            elif success_count == 0:
                console.print("[red]Failed to fetch any covers[/red]")
                return 1
            else:
                console.print(f"[yellow]Partially successful: fetched {success_count} out of {total} covers[/yellow]")
                return 1
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1