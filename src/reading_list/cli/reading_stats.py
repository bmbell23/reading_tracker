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
    author_stats_parser = stats_subparsers.add_parser(
        "author-stats",
        help="Display statistics about books read by author"
    )
    author_stats_parser.add_argument(
        "--all",
        action="store_true",
        help="Show all authors with reading sessions, including those without owned books"
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
        
        # By default, only show authors with owned books or completed reads
        if not args.all:
            author_stats = [stat for stat in author_stats 
                          if stat['unique_books_completed'] > 0 or stat['total_books_owned'] > 0]
        
        table = Table(
            title="[bold cyan]Reading Statistics by Author[/bold cyan]",
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
            padding=(0, 1)
        )
        
        # Add columns with enhanced formatting
        table.add_column("Author", style="cyan", no_wrap=True)
        table.add_column("📚 Books\nOwned", justify="right", style="magenta")
        table.add_column("✨ Unique\nReads", justify="right", style="magenta")
        table.add_column("🔄 Total\nReads", justify="right", style="magenta")
        table.add_column("📅 Future\nReads", justify="right", style="magenta")
        
        for stat in author_stats:
            # Convert "Last, First" to "First Last"
            author_parts = stat['author'].split(', ', 1)
            if len(author_parts) == 2:
                author_name = f"{author_parts[1]} {author_parts[0]}"
            else:
                author_name = stat['author']

            table.add_row(
                author_name,  # Use reformatted name here
                str(stat['total_books_owned']),
                str(stat['unique_books_completed']),
                str(stat['total_reading_sessions']),
                str(stat['future_reads'])
            )
        
        # Add some spacing and a header
        console.print("\n[bold blue]📚 Author Reading Statistics[/bold blue]")
        console.print("[dim]Shows reading patterns across your library[/dim]\n")
        
        # Print the table
        console.print(table)
        
        # Add a footer with totals
        totals = {
            'books_owned': sum(stat['total_books_owned'] for stat in author_stats),
            'unique_completed': sum(stat['unique_books_completed'] for stat in author_stats),
            'completed_readings': sum(stat['total_reading_sessions'] for stat in author_stats),
            'future_reads': sum(stat['future_reads'] for stat in author_stats)
        }
        
        console.print("\n[bold blue]📊 Summary[/bold blue]")
        console.print(f"Total Books Owned: [blue]{totals['books_owned']:,}[/blue]")
        console.print(f"Total Unique Books Completed: [green]{totals['unique_completed']:,}[/green]")
        console.print(f"Total Reading Sessions: [yellow]{totals['completed_readings']:,}[/yellow]")
        console.print(f"Total Future Reads: [magenta]{totals['future_reads']:,}[/magenta]\n")
        
        return 0
    
    elif args.stats_command == "debug-author":
        queries.debug_author_books(args.first_name, args.last_name)
        return 0
    
    else:
        console.print("[red]Please specify a statistics command (e.g., author-stats)[/red]")
        return 1
