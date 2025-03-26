"""CLI command for generating reading statistics."""
from rich.console import Console
from rich.table import Table
from ..queries.common_queries import CommonQueries

console = Console()

def add_subparser(subparsers):
    """Add reading-stats commands to the CLI parser."""
    parser = subparsers.add_parser(
        "reading-stats",
        help="Commands for generating reading statistics"
    )
    
    # Add subcommands
    stats_subparsers = parser.add_subparsers(dest="stats_command", help="Available statistics commands")
    
    # Author stats command
    stats_subparsers.add_parser(
        "author-stats",
        help="Display statistics about books read by author"
    )
    
    # Debug author command
    debug_parser = stats_subparsers.add_parser(
        "debug-author",
        help="Show detailed information about an author's books"
    )
    debug_parser.add_argument("first_name", help="Author's first name")
    debug_parser.add_argument("last_name", nargs='?', help="Author's last name")

    return parser

def handle_command(args):
    """Handle reading-stats commands."""
    queries = CommonQueries()
    
    if args.stats_command == "author-stats":
        author_stats = queries.get_books_by_author()
        
        if not author_stats:
            console.print("[yellow]No author statistics found[/yellow]")
            return 0
        
        table = Table(title="Reading Statistics by Author")
        table.add_column("Author", style="cyan")
        table.add_column("Books\nOwned", justify="right", style="blue")
        table.add_column("Unique\nBooks\nRead", justify="right", style="magenta")
        table.add_column("Finished\nReading\nSessions", justify="right", style="green")
        table.add_column("Future\nReading\n Sessions", justify="right", style="yellow")
        
        for stat in author_stats:
            table.add_row(
                stat['author'],
                str(stat['total_books_owned']),
                str(stat['unique_books_completed']),
                str(stat['total_reading_sessions']),
                str(stat['future_reads'])
            )
        
        console.print(table)
        return 0
    
    elif args.stats_command == "debug-author":
        queries.debug_author_books(args.first_name, args.last_name)
        return 0
    
    else:
        console.print("[red]Please specify a statistics command (e.g., author-stats)[/red]")
        return 1
