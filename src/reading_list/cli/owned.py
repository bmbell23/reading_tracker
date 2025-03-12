"""CLI command for displaying owned books by format."""
import argparse
from rich.console import Console
from rich.table import Table
from ..queries.common_queries import CommonQueries

console = Console()

def create_books_table(title: str) -> Table:
    """Create a formatted table for displaying books."""
    table = Table(
        title=title,
        show_header=True,
        header_style="bold magenta",
        border_style="bright_black"
    )
    
    table.add_column("BID", justify="right", style="cyan")
    table.add_column("RID", justify="right", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Author", style="white")
    table.add_column("Pages", justify="right", style="blue")
    table.add_column("Words", justify="right", style="blue")
    table.add_column("Location", style="green")
    table.add_column("Status", style="yellow")
    
    return table

def display_books(books: list, format_type: str):
    """Display books in a formatted table."""
    if not books:
        console.print(f"\n[yellow]No {format_type} books found.[/yellow]")
        return

    title = f"Owned {format_type.capitalize()} Books"
    table = create_books_table(title)
    
    # Initialize counters
    total_books = 0
    total_read = 0
    total_words = 0
    total_pages = 0
    
    for book in books:
        total_books += 1
        if book['reading_status'] == 'completed':
            total_read += 1
        total_words += book['words'] or 0
        total_pages += book['pages'] or 0
        
        table.add_row(
            str(book['book_id']),
            str(book['reading_id']) if book['reading_id'] else "-",
            book['title'],
            book['author'],
            str(book['pages'] or ''),
            f"{book['words']:,}" if book['words'] else '',
            book['location'] or '',
            book['reading_status']
        )
    
    # Add a separator before totals
    table.add_section()
    
    # Add totals row
    table.add_row(
        "[bold]TOTALS[/bold]",
        "",
        f"[bold]{total_books:,} books[/bold]",
        f"[bold]{total_read:,} read[/bold]",
        f"[bold]{total_pages:,}[/bold]",
        f"[bold]{total_words:,}[/bold]",
        "",
        f"[bold]{(total_read/total_books*100):.1f}% complete[/bold]" if total_books > 0 else "-"
    )
    
    console.print(table)
    
    # Print summary below table
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"📚 Total Books: [cyan]{total_books:,}[/cyan]")
    console.print(f"✅ Books Read: [green]{total_read:,}[/green] ([yellow]{(total_read/total_books*100):.1f}%[/yellow])" if total_books > 0 else "")
    console.print(f"📄 Total Pages: [blue]{total_pages:,}[/blue]")
    console.print(f"📝 Total Words: [blue]{total_words:,}[/blue]")
    console.print(f"📊 Average Pages per Book: [magenta]{(total_pages/total_books):.1f}[/magenta]" if total_books > 0 else "")
    console.print(f"📊 Average Words per Book: [magenta]{(total_words/total_books):,.1f}[/magenta]" if total_books > 0 else "")

def add_subparser(subparsers):
    """Add the owned command parser to the main parser."""
    parser = subparsers.add_parser(
        "owned",
        help="Display owned books by format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all owned books
  reading-list owned

  # Show only physical books
  reading-list owned --physical

  # Show only Kindle books
  reading-list owned --kindle

  # Show only audiobooks
  reading-list owned --audio
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--physical",
        action="store_true",
        help="Show only physical books"
    )
    group.add_argument(
        "--kindle",
        action="store_true",
        help="Show only Kindle books"
    )
    group.add_argument(
        "--audio",
        action="store_true",
        help="Show only audiobooks"
    )
    
    return parser

def handle_command(args):
    """Handle the owned command."""
    try:
        queries = CommonQueries()
        
        if args.physical:
            display_books(queries.get_owned_books_by_format('physical'), 'physical')
        elif args.kindle:
            display_books(queries.get_owned_books_by_format('kindle'), 'kindle')
        elif args.audio:
            display_books(queries.get_owned_books_by_format('audio'), 'audio')
        else:
            # Show all formats
            all_books = queries.get_all_owned_books()
            display_books(all_books['physical'], 'physical')
            display_books(all_books['kindle'], 'kindle')
            display_books(all_books['audio'], 'audio')
        
        return 0
    except Exception as e:
        console.print(f"[red]Error displaying owned books: {str(e)}[/red]")
        return 1