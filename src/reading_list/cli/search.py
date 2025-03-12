"""CLI command for searching readings by title."""
import argparse
from rich.console import Console
from ..queries.common_queries import CommonQueries

console = Console()

def add_subparser(subparsers):
    """Add the search command parser to the main parser."""
    parser = subparsers.add_parser(
        "search",
        help="Search readings by title",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for readings with 'dune' in the title
  reading-list search dune

  # Search for exact title match
  reading-list search "Dune" --exact
        """
    )

    parser.add_argument(
        "title",
        help="Title or part of title to search for"
    )

    parser.add_argument(
        "--exact",
        "-e",
        action="store_true",
        help="Search for exact title match"
    )

    return parser

def handle_command(args):
    """Handle the search command."""
    try:
        queries = CommonQueries()
        queries.print_readings_by_title(args.title, exact_match=args.exact)
        return 0
    except Exception as e:
        console.print(f"[red]Error searching readings: {str(e)}[/red]")
        return 1