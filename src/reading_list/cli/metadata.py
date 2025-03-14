"""CLI command for fetching book metadata."""
import argparse
from rich.console import Console
from ..services.metadata_fetcher import MetadataFetcher

console = Console()

def add_subparser(subparsers):
    """Add the metadata command parser to the main parser."""
    parser = subparsers.add_parser(
        "metadata",
        help="Fetch and update book metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all metadata
  reading-list metadata --all

  # Fetch only book covers
  reading-list metadata --covers

  # Force update existing metadata
  reading-list metadata --all --force-update

  # Fetch pages only for books without page counts
  reading-list metadata --pages --missing-only
        """
    )
    
    # Change these to be mutually exclusive
    metadata_group = parser.add_mutually_exclusive_group(required=True)
    metadata_group.add_argument('--all', action='store_true',
                       help='Fetch all available metadata')
    metadata_group.add_argument('--covers', action='store_true',
                       help='Fetch book covers')
    metadata_group.add_argument('--isbn', action='store_true',
                       help='Fetch ISBN numbers')
    metadata_group.add_argument('--dates', action='store_true',
                       help='Fetch publication dates')
    metadata_group.add_argument('--pages', action='store_true',
                       help='Fetch page counts')
    metadata_group.add_argument('--words', action='store_true',
                       help='Fetch word counts')
    metadata_group.add_argument('--series', action='store_true',
                       help='Fetch series information')
    metadata_group.add_argument('--author', action='store_true',
                       help='Fetch author information')
    
    parser.add_argument('--force-update', action='store_true',
                       help='Force update of metadata, even if it already exists')
    parser.add_argument('--missing-only', action='store_true',
                       help='Only update entries that are missing the requested metadata')
    parser.add_argument('--concurrent-requests', type=int, default=10,
                       help='Maximum number of concurrent API requests')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of worker threads for file operations')
    
    return parser

def handle_command(args):
    """Handle the metadata command."""
    try:
        fetcher = MetadataFetcher(
            force_update=args.force_update,
            missing_only=args.missing_only
        )
        fetcher.max_concurrent_requests = args.concurrent_requests
        fetcher.max_workers = args.workers

        if args.all:
            fetcher.fetch_all_metadata()
        elif args.covers:
            fetcher.fetch_covers()
        elif args.isbn:
            fetcher.fetch_isbns()
        elif args.dates:
            fetcher.fetch_publication_dates()
        elif args.pages:
            fetcher.fetch_page_counts()
        elif args.words:
            fetcher.fetch_word_counts()
        elif args.series:
            fetcher.fetch_series_info()
        elif args.author:
            fetcher.fetch_author_info()
        else:
            console.print("[yellow]No metadata type specified. Use --help to see available options.[/yellow]")
            return 1

        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
